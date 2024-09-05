import connexion
import six

from swagger_server import util
from astropy.io import fits
from flask import send_file
from flask import request
import io
import tesis_opt
import zipfile
import pandas as pd
import os
import time
from delight import *
import subprocess

import cProfile, pstats, io

import multiprocessing

import shutil

import tarfile

def get_files2(dataframe, output_dir):
    """Worker function to process a chunk of the DataFrame and write FITS files to output_dir."""
    for idx, row in dataframe.iterrows():
        for k in range(5):
            fits_data = tesis_opt.fits_cutout(row.ra, row.dec, 11 - k, 30)
            folder_path = os.path.join(output_dir, f'multiresolution_fits_files/{row.oid}')
            os.makedirs(folder_path, exist_ok=True)
            fits_file_path = os.path.join(folder_path, f"{row.oid}_order{11 - k}.fits")
            # Write FITS data to file
            with open(fits_file_path, 'wb') as f:
                fits_data.writeto(f, overwrite=True)


def get_files(dataframe, chunk_index):
    """Worker function to process chunks of the dataframe and write to a temporary ZIP file."""
    B = {}
    temp_zip_path = f"/tmp/temp_zip_{chunk_index}.zip"
    inicio=time.time()
    with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, oid in dataframe.iterrows():
            A = []
            ra, dec, oid_str = oid['ra'], oid['dec'], str(oid['oid'])
            
            for k in range(5):
                # Replace this with your actual method to get FITS cutout
                try:
                    A.append([tesis_opt.fits_cutout(ra, dec, 11 - k, 30), ra, dec, 11 - k, oid_str])
                except(FileNotFoundError):
                    print("WARNING: " + str(ra) +"," + str(dec))
            
            B[oid_str] = A
        print(time.time()-inicio)    
        for folder, files in B.items():
            folder_path = os.path.join('multiresolution_fits_files', folder)
            zip_file.writestr(folder_path + '/', '')

            for filename in files:
                hdulist = filename[0]
                with io.BytesIO() as fits_binary_data:
                    hdulist.writeto(fits_binary_data, checksum=True, overwrite=True)
                    fits_binary_data.seek(0)
                    zip_file.writestr(os.path.join(folder_path, f"{filename[4]}_order{filename[3]}.fits"), fits_binary_data.getvalue())
                hdulist.close()
    print(time.time()-inicio)
    return temp_zip_path

def worker(queue, dataframe, chunk_index):
    """Worker function to process chunks of the dataframe and put the path to the ZIP file into the queue."""
    zip_path = get_files(dataframe, chunk_index)
    queue.put(zip_path)  # Enqueue the path to the result queue

def combine_zip_files(output_zip, temp_zip_paths):
    """Combine multiple ZIP files into a single ZIP file."""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as output_zip_file:
        for temp_zip_path in temp_zip_paths:
            if temp_zip_path and os.path.exists(temp_zip_path):
                with zipfile.ZipFile(temp_zip_path, 'r') as temp_zip_file:
                    for item in temp_zip_file.infolist():
                        output_zip_file.writestr(item, temp_zip_file.read(item.filename))
            else:
                print(f"Warning: {temp_zip_path} does not exist or is not valid.")
    
            

target_header = fits.Header.fromstring("""
NAXIS   =                    2
NAXIS1  =                  30
NAXIS2  =                  30
CTYPE1  = 'RA---TAN'
CRPIX1  =                15
CRVAL1  =                3.5
CDELT1  =               6.94444461259988E-05
CUNIT1  = 'deg     '
CTYPE2  = 'DEC--TAN'
CRPIX2  =                15
CRVAL2  =                2.5
CDELT2  =                6.94444461259988E-05
CUNIT2  = 'deg     '
COORDSYS= 'icrs    '
PC001001=                  -1.
PC001002=                   0.
PC002001=                   0.
PC002002=                   1.
""", sep='\n')




def query_multiresolution_ra_dec_get(ra, dec):  # noqa: E501
    """Set of 5 multiresolution images

    Retrieves the requested set of 5 multiresolution images wich delight would use. # noqa: E501

    :param ra: 
    :type ra: float
    :param dec: 
    :type dec: float

    :rtype: str
    """
    fits_files=[]
    for i in range(5):
        try:
            fits_files.append(tesis_opt.fits_cutout(ra,dec,11-i,30))
        except(FileNotFoundError):
            return
    zip_buffer = io.BytesIO()

    a = "order"
    b = 11

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in fits_files:
            # Open each FITS file
            hdulist = filename

            # Get the primary HDU
            primary_hdu = hdulist[0]

            # Get the binary data of the FITS file
            fits_binary_data = io.BytesIO()
            primary_hdu.writeto(fits_binary_data, checksum=True, overwrite=True)
            fits_binary_data.seek(0)  # Move the pointer to the beginning of the buffer

            # Add the FITS file to the zip file
            zip_file.writestr(a+str(b)+".fits", fits_binary_data.read())
            b = b-1

    zip_buffer.seek(0)

    # Return the zip file as a file attachment
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='fits_files.zip')


def query_stamp_ra_dec_order_size_get(ra, dec, order, size):  # noqa: E501
    """Fits image

    Retrieve the requested astronomic image, centered in (ra,dec) and with dimensions (size x size). # noqa: E501

    :param ra: 
    :type ra: float
    :param dec: 
    :type dec: float
    :param order: 
    :type order: int
    :param size: 
    :type size: int

    :rtype: str
    """
    try:
        hdul = tesis_opt.fits_cutout(ra,dec,order,size)
    except(FileNotFoundError):
        print("The object is not currently available.")
        return str("The object is not currently available.") 
    primary_hdu = hdul[0]
    fits_data_io = io.BytesIO()
    primary_hdu.writeto(fits_data_io)
    fits_data_io.seek(0) 
    title = str(round(ra,4))+"_"+str(round(dec,4))+"_order"+str(order)+"_N"+str(size)+".fits"

    return send_file(fits_data_io, mimetype='application/octet-stream',
            as_attachment=True, download_name=title)


def query_objects_ra_dec_get(filename):
    df = pd.read_csv(filename)
    temp_dir = '/tmp/fits_files'
    tar_path = '/tmp/fits_archive.tar.gz'

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)  # Clean up the directory if it exists
    os.makedirs(temp_dir)

    manager = multiprocessing.Manager()
    jobs = []
    num_chunks = 10
    chunk_size = len(df) // num_chunks

    inicio = time.time()
    for i in range(num_chunks):
        start_index = i * chunk_size
        end_index = (i + 1) * chunk_size if i < num_chunks - 1 else len(df)
        p = multiprocessing.Process(target=get_files2, args=(df[start_index:end_index], temp_dir))
        jobs.append(p)
        p.start()

    for proc in jobs:
        proc.join()

    print(f"Image generation time: {time.time() - inicio} seconds")

    inicio2 = time.time()

    # Crear un archivo TAR a partir del directorio
    with tarfile.open(tar_path, 'w') as tar:
        tar.add(temp_dir, arcname=os.path.basename(temp_dir))

    print(f"TAR time: {time.time() - inicio2} seconds")
        
    # Servir el archivo TAR
    response = send_file(tar_path, mimetype='application/x-tar', as_attachment=True, download_name='fits_files.tar.gz')

    shutil.rmtree(temp_dir)
    os.remove(tar_path)

    return response   


def query_objects_ra_dec_post():
    """Retrieve FITS files, store them in a directory, and compress the directory into a ZIP file."""
    df = pd.read_csv(request.files['file'])

    temp_dir = '/tmp/fits_files'
    tar_path = '/tmp/fits_archive.tar.gz'

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)  # Clean up the directory if it exists
    os.makedirs(temp_dir)

    manager = multiprocessing.Manager()
    jobs = []
    num_chunks = 10
    chunk_size = len(df) // num_chunks

    inicio = time.time()
    for i in range(num_chunks):
        start_index = i * chunk_size
        end_index = (i + 1) * chunk_size if i < num_chunks - 1 else len(df)
        p = multiprocessing.Process(target=get_files2, args=(df[start_index:end_index], temp_dir))
        jobs.append(p)
        p.start()

    for proc in jobs:
        proc.join()

    print(f"Image generation time: {time.time() - inicio} seconds")

    inicio2 = time.time()

    # Crear un archivo TAR a partir del directorio
    with tarfile.open(tar_path, 'w') as tar:
        tar.add(temp_dir, arcname=os.path.basename(temp_dir))

    print(f"TAR time: {time.time() - inicio2} seconds")
        
    # Servir el archivo TAR
    response = send_file(tar_path, mimetype='application/x-tar', as_attachment=True, download_name='fits_files.tar.gz')

    shutil.rmtree(temp_dir)
    os.remove(tar_path)

    return response

def query_delight_ra_dec_get(ra, dec,host=False):  # noqa: E501
    """Set of 5 multiresolution images

    Retrieves the requested set of 5 multiresolution images wich delight would use. # noqa: E501

    :param ra: 
    :type ra: float
    :param dec: 
    :type dec: float

    :rtype: str
    """

    df = pd.DataFrame({ "oid": ["SN2004aq"], "ra": [ra], "dec": [dec]})
    dclient = Delight("/home/dleon/DF", df.oid.values, df.ra.values, df.dec.values)
    try:
        dclient.download(overwrite=True)
    except(FileNotFoundError):
        return {"ra" : "NaN", "dec" : "NaN", "comment" : "The object is not currently available."}
    dclient.get_pix_coords()
    nlevels = 5
    domask = False
    doobject = True
    doplot = False
    dclient.compute_multiresolution(nlevels, domask, doobject, doplot)
    
    dclient.load_model(modelfile="DELIGHT_v1.h5")
    dclient.preprocess()
    dclient.predict()
    print(dclient.df)

    if(host):
        dclient.get_hostsize("SN2004aq",doplot=False)
        return {"ra" : dclient.df.ra_delight[0], "dec" : dclient.df.dec_delight[0], "hostsize" :  dclient.df.hostsize[0]} 
    else:
        return {"ra" : dclient.df.ra_delight[0], "dec" : dclient.df.dec_delight[0]} 

