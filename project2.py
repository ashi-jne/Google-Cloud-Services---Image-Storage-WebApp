
"""
Project 3 requirements:

    - Implement change management to your application and create automation for deployment as well as automated testing

    - Upon completion 50% of your users should see a blue background, while the other 50% should see a green background on your front layer

    - Traffic should be split evenly and you should be able to run the 2 versions of the application in parallel

    - Do not implement the split logic in your application.

    - EXTRA POINTS for considering different development and staging environments as well as automated rollback should your tests fail

    - (from Project 2): EXTRA POINTS for considering multiple users and protecting their images from other users’ access

"""

"""
Develpment environment setup (for Windows): https://cloud.google.com/python/docs/setup#windows

"""

import os
import uuid
import time

from flask import Flask, redirect, request, redirect, render_template
from werkzeug.utils import secure_filename

from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter
from google.cloud import storage 

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'JPG', 'JPEG'}

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

g_project_name = 'group17-project2'
g_project_id = 'group17-project1-399506'
g_bucket_name = 'project2-repo'

g_datastore_query_by_kind = 'ImageMetadata'

## ------------------------------------------------------------      

class ImageMetadata:
    """
    Use this class to create am image file's metadata for insertion in the Cloud Datastore

    Multiple ctor's in Python: 

        1. https://www.geeksforgeeks.org/what-is-a-clean-pythonic-way-to-have-multiple-constructors-in-python/
    
        2. https://realpython.com/python-multiple-constructors/#:~:text=Using%20the%20%40classmethod%20decorator%20to,to%20provide%20multiple%20alternative%20constructors.

    """  

    def __init__(self, filepathspec, owner, location):
        name_parts = filepathspec.split('/')
        self._filename = name_parts[-1]
        self._id = uuid.uuid4()

        self._owner = owner
        self._location = location

        stats = os.stat(filepathspec)
        self._size = stats.st_size      # in bytes

        fileModTime = os.path.getctime(filepathspec)    
        self._createDate = time.strftime("%Y-%m-%d %I:%M:%S %p", time.localtime(fileModTime))        

    def get_filename(self):
        return self._filename
    
    def get_id(self):
        return self._id
    
    def get_owner(self):
        return self._owner
    
    def get_location(self):
        return self._location
    
    def get_size(self):
        return self._size
    
    def get_date(self):
        return self._createDate
    
    def upload_to_datastore(self):
        """
        Create a Cloud Datastore entity for the image
        """
        client = datastore.Client(g_project_id)
        image_key = client.key(g_datastore_query_by_kind, str(self._id))
        image_entity = datastore.Entity(key=image_key)
        image_entity.update({
            "filename": self._filename,
            "owner": self._owner,
            "location": self._location,
            "size": self._size,
            "createDate": self._createDate
        })

        # Save the entity in Datastore
        client.put(image_entity)


## ------------------------------------------------------------     

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

## ------------------------------------------------------------ 

@app.route('/')
@app.route('/index')
def index():
    file_link_tuple = get_file_link_tuple()
    return render_template('index.html', file_link_tuple = file_link_tuple)


@app.route('/upload', methods = ['POST'])   
def upload():
    file = request.files['file_select_form'] 
    
    if (file and allowed_file(file.filename)):
        filename = secure_filename(file.filename)

        # save temporarily to server folder, for upload to CStorage and metadata retreival and upload to CDatastore
        file.save(filename) 

        # upload file to CStorage 
        #
        client = storage.Client(g_project_name)
        bucket = client.get_bucket(g_bucket_name)

        blob = bucket.blob(filename)
        blob.upload_from_filename(filename, content_type='image/jpeg')

        if blob.public_url != None:
            location = blob.public_url
        else:
            location = blob.media_link

        # upload metadata to CDatastore (Firestore) 
        #
        metadata = ImageMetadata(filename, 'app_user', location)
        metadata.upload_to_datastore()

    # send user back to Home page, where file display should be updated
    return redirect("/")  


def get_photo_metadata(public_url):
    """
    query CDatastore for the photo's metadata using its public URL as the key
    """
    client = datastore.Client(g_project_id)
    query = client.query(kind=g_datastore_query_by_kind)

    query.add_filter(filter=PropertyFilter('location', '=', public_url))

    result = list(query.fetch(limit=1))
    if result:       
        photo = result[0]
        metadata = {
            "filename": photo["filename"],
            "imageUrl": photo["location"],
            "uploadDate": photo["createDate"],
            "size": photo["size"],
            "owner": photo["owner"]
        }       
        return metadata     # returns the photo's metadata as a dictionary
    else:
        return None     


def get_file_link_tuple():
    pathspec = []
    filesize = []
    dataStoreUrl = []
    fileName = []
    createDate = []

    client = storage.Client(g_project_name)
    blobs = client.list_blobs(g_bucket_name)

    for blob in blobs:
        metadata = get_photo_metadata(blob.public_url)     

        if (metadata != None):
            pathspec.append(blob.public_url)   
            filesize.append('{:.0f} KB'.format(metadata['size']/1024))   
            dataStoreUrl.append(metadata['imageUrl'])
            fileName.append(metadata['filename'])
            createDate.append(metadata['uploadDate'])

            blob.download_to_filename(metadata['filename']) 

    file_link_tuple = list(zip(fileName, pathspec, filesize, dataStoreUrl, createDate))
    return file_link_tuple

# ----------------------------------------------------------------------------
# run the server-side app
#
app.run(host='0.0.0.0', port=8080)
