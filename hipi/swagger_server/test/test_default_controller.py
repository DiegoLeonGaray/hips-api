# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_query_multiresolution_ra_dec_get(self):
        """Test case for query_multiresolution_ra_dec_get

        Set of 5 multiresolution images
        """
        query_string = [('ra', 240.34),
                        ('dec', 26.29)]
        response = self.client.open(
            '/query_multiresolution',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_query_objects_ra_dec_get(self):
        """Test case for query_objects_ra_dec_get

        Get a list of several sets of 5 multiresolution images
        """
        query_string = [('filename', 'test_delight.csv')]
        response = self.client.open(
            '/query_objects',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_query_objects_ra_dec_post(self):
        """Test case for query_objects_ra_dec_post

        CSV file to multiresolution images
        """
        data = dict(file='/test_delight.csv')
        response = self.client.open(
            '/query_objects',
            method='POST',
            data=data,
            content_type='multipart/form-data')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_query_stamp_ra_dec_order_size_get(self):
        """Test case for query_stamp_ra_dec_order_size_get

        Fits image
        """
        query_string = [('ra', 240.34),
                        ('dec', 26.29),
                        ('order', 11),
                        ('size', 512)]
        response = self.client.open(
            '/query_stamp',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
