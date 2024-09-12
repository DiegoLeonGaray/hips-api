# hips-api

Fast generation of multi-resolution astronomical images for the AlERCE proyect. 

Generation of images required by the DELIGHT algorithm using a local HiPS server.

## Dependencies

- Libraries to be installed are described in [*requirements.txt*](https://github.com/DiegoLeonGaray/hips-api/blob/main/hipi/requirements.txt).

- Local HiPS server.

## API Endpoints

### query_stamp

#### GET

- DESCRIPTION: 
Retrieve the requested astronomic image, centered in (ra,dec) and with dimensions (size x size).

- PARAMETERS: 
    1) ra: Required right ascension. (MIN=0, MAX=360)

    2) dec: Required declination. (MIN=0, MAX=90)

    3) order: HiPS order to use in image generation. Order 11: 0.25''/pixel.
         Order 10: 0.5''/pixel. Order 9: 1''/pixel. Order 8: 2''/pixel. Order 7: 4''/pixel. (MIN=7, MAX=11)

    4) size: Size in pixels of the required image. (MIN=15, MAX=512)

### query_multiresolution

#### GET

- DESCRIPTION: 
Recovers the set of multi-resolution images that DELIGHT requires.

- PARAMETERS:
    1) ra: Required right ascension. (MIN=0, MAX=360)

    2) dec: Required declination. (MIN=0, MAX=90)

### query_objects

#### GET

- DESCRIPTION:
Recovers multiple sets of multiresolution images that DELIGHT requires, using coordinates in a CSV file.

- PARAMETERS:
    1) filename: Path of the file in the server. The file must include at least the following columns:

        `oid, ra, dec`

    2) gz (optional): Boolean to indicate if you want to compress the resulting file.

#### POST

- DESCRIPTION:
Recovers multiple sets of multiresolution images that DELIGHT requires, using coordinates in a CSV file. The file must include at least the following columns:

    `oid, ra, dec`

### query_delight

#### GET

- DESCRIPTION:


- PARAMETERS:
    1) ra: Required right ascension. (MIN=0, MAX=360)

    2) dec: Required declination. (MIN=0, MAX=90)

    3) host (optional): Do you want the host size prediction?




