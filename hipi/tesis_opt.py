#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  5 13:55:59 2023

@author: diegoleon
"""



import numba


import healpy as hp
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import numpy as np





"""

Definición de algunas variables globales necesarias para algunos cálculos relacionados 
con los pixeles tanto de la imagen resultante como de las imágenes a procesar.
 
================
 
int[480] A : Arreglo que enumera desde 0 hasta 479.

int[480][480] M1: Matriz donde cada fila es igual al arreglo A.

int[480][480] M2: Matriz donde la fila i se rellena sólo con enteros iguales a i.

{int, float} D: Diccionario el cual relaciona el orden HiPS con la resolución por pixel de la imagen a retornar.

Astropy.FitsHeader target_header: Header del archivo .fits que se retornará.


================

"""

A=np.arange(0,480,1)
M1 = np.zeros((480,480))
M2 = np.zeros((480,480))

for i in range(len(M1)):
    M1[i]=A
    M2[i]=M2[i]+i

D = {}

D[11]=6.94444461259988E-05
D[10]=D[11]*2
D[9]=D[10]*2
D[8]=D[9]*2
D[7]=D[8]*2

target_header = fits.Header.fromstring("""
NAXIS   =                    2
NAXIS1  =                  512
NAXIS2  =                  512
CTYPE1  = 'RA---TAN'
CRPIX1  =                256
CRVAL1  =                
CDELT1  =               6.94444461259988E-05
CUNIT1  = 'deg     '
CTYPE2  = 'DEC--TAN'
CRPIX2  =                256
CRVAL2  =                
CDELT2  =                6.94444461259988E-05
CUNIT2  = 'deg     '
COORDSYS= 'icrs    '
PC001001=                  -1.
PC001002=                   0.
PC002001=                   0.
PC002002=                   1.
""", sep='\n')



"""

La función "calculator" recibe toda la información recuperada y almacenada por
el algoritmo en forma de numpy array, para realizar el cálculo del pixel más
cercano para todos los pixeles de interés, utilizando decoradores Numba para
acelerar el proceso.

Primero se recupera el índice del archivo HiPS que contiene a la coordenada 
que representa al pixel (i,j), para luego establecer el valor del pixel (i,j)
como el valor del pixel en el archivo HiPS el cual es más cercano a la 
coordenada de interés.

"""

@numba.njit()
def calculator(data,tiles,NearPix,images,coordTile,size):
    for i in range(size):
        for j in range(size):
            indice=np.where(tiles==coordTile[i][j])[0][0]
            data[j][i]=images[indice][int(np.round(NearPix[indice][1][i][j]))][int(np.round(NearPix[indice][0][i][j]))]
    return data


def fits_cutout(ra,dec,order,NN):
    """
    
    Parameters
    ----------
    ra : Float
        Ascención recta que define el centro de la imagen a retornar.
    dec : Float
        Declinación que define el centro de la imagen a retornar.
    order : Int
        Orden HiPS solicitado para la imagen a retornar.
    NN : Int
        Tamaño en pixeles de la imagen a retornar.

    Returns
    -------
    hdul : HDUList
        Objeto HDUList del módulo astropy.io.fits que representa el archivo
        fits retornado.

    """
    
    
    
    target_header["CRVAL1"]=ra
    target_header["CRVAL2"]=dec
    target_header["NAXIS1"]=NN
    target_header["NAXIS1"]=NN
    target_header["CRPIX1"]=NN/2
    target_header["CRPIX2"]=NN/2
    target_header["CDELT1"]=D[order]
    target_header["CDELT2"]=D[order]
    


    side=hp.order2nside(order)
    
    data_fits=np.zeros((NN,NN)) #Matriz que representará la imagen a retornar.



    """
    Ya teniendo el header definido y la forma de ingresar a los índices eficientemente,
    utilizamos la función "pixel_to_world_values" del módulo WCS para almacenar en una
    variable las coordenadas celestes de los pixeles (i,j), con 0<=i<=NN y 0<=j<=NN.

    La variable Coords, almacena en su primer elemento una matriz tal que Coords[0][i][j]
    corresponde a la ascención recta del pixel (i,j). En su segundo elemento, almacena
    una matriz tal que Coords[1][i][j] corresponde a la declinación del pixel (i,j)

    """
        

    w = WCS(target_header)
    Coords = w.pixel_to_world_values(M2[0:NN,0:NN],M1[0:NN,0:NN])



    
    """
    Obtenemos Las imágenes HiPS que cubren al corte .fits pedido. 

    Tiles : Arreglo que contiene los índices de
    los HiPS tiles de interés.

    Images : Arreglo que contiene la data de los HiPS tiles pertenecientes 
    a Tiles. Images[i] contiene los pixeles del HiPS tile Tiles[i].
    
    WE : Arreglo que contiene a los objetos de la clase WCS obtenidos a partir
    de los HiPS tiles. WE[i] contiene al objeto WCS del archivo HiPS Tiles[i].
    
    CoordToTile : Matriz que contiene la información sobre la relación entre coordenadas
    celestes y archivo HiPS. CoordToTile[i][j] representa al HiPS tile que contiene a la
    coordenada celeste del pixel [i][j] de la imagen a retornar.


    """

    

    CoordToTile = hp.ang2pix(side,Coords[0],Coords[1],nest=True,lonlat=True)
    sky = SkyCoord(Coords[0], Coords[1], frame='icrs', unit='deg')
    Tiles = np.unique(CoordToTile)
    
    Images =[]
    WE = []


    for i in Tiles:
        y=(i//10000)*10000
        dire1='Dir'+str(y)
        npix1='Npix'+str(i)+'.fits'
        image1=fits.open('/Users/diegoleon/Desktop/tesis/HiPS_DELIGHT/Norder'+str(order)+'/'+dire1+'/'+npix1)
        data1=image1[0].data
        Images.append(data1)
        WE.append(WCS(image1[0].header))
    

    """

    Teniendo la matriz CoordToTile, solo resta obtener la información sobre
    el pixel más cercano. Se necesita el pixel del archivo CoordToTile[i][j]
    el cual es más cercano a la coordenada que representa al pixel [i][j] de
    la imagen a retornar. 
    
    NearestPixels: Teniendo en cuenta el archivo Tiles[k], NearestPixels[k][1][i][j]
    representa la posición "i" (horizontal) del pixel del archivo Tiles[k] el cual es más cercano
    a la coordenada (i,j). NearestPixels[k][0][i][j] representa la posición "j" (vertical)
    del pixel del archivo Tiles[k] el cual es más cercano a la coordenada (i,j). 
    

    """

    NearestPixels=[]

    for i in WE:
        NearestPixels.append(i.world_to_pixel(sky))
        
    """
    
    Teniendo toda la información necesaria para el cálculo del valor de cada pixel a 
    retornar, se debe traspasar tal información a numpy arrays para que sea posible
    la optimización del cálculo a través de deprecadores Numba.
    
    """
    
        
    Images=np.array(Images,dtype='float32')
    Tiles=np.array(Tiles)
    WE=np.array(WE)
    NearestPixels=np.array(NearestPixels)
    
    
    
    
        
    data_fits = calculator(data_fits,Tiles,NearestPixels,Images,CoordToTile,NN)
    hdu = fits.PrimaryHDU(data_fits,header=target_header)
    hdul = fits.HDUList([hdu])
    return hdul



"""
Función write_image Posibilita la escritura en sistema de las imágenes generadas.
"""

def write_image(fits_image, title, out_dir):
    """
    
    Parameters
    ----------
    fits_image : HDUList
        Archivo fits a escribir.
    title : String
        Título del archivo a escribir.
    out_dir : String
        Directorio del archivo a escribir.

    Returns
    -------
    None.

    """

    fits_image.writeto(out_dir+'/'+title+'.fits',overwrite=True)
    
    
    
    
    






