from flask import jsonify 
import pyrebase
import firebase_admin
from pyrebase.pyrebase import storage  
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import secretmanager
import firebase_admin
from firebase_admin import storage as admin_storage, credentials, firestore
import os
import json
from firebase_admin import credentials, initialize_app
import os
import uuid
import time
from flask import Flask, redirect, request, redirect, render_template, session
from werkzeug.utils import secure_filename
from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter
from google.cloud import storage 
from firebase_admin import auth
from datetime import datetime
from firebase_admin import storage, firestore
from google.cloud import exceptions
# Initialize without explicit credentials since GCP manages it



app=Flask(__name__)
#Ideally, this should be stored in secret manager.
app.secret_key = 'your-hardcoded-secret-key'


client = secretmanager.SecretManagerServiceClient()

# Specify the name of your secret in Secrets Manager
secret_name = ""

# Access the secret
response = client.access_secret_version(request={"name": secret_name})
secret_payload = response.payload.data.decode("UTF-8")
# Other imports remain unchanged

# Decode the secret payload into a service account info dictionary
service_account_info = json.loads(secret_payload)

# Initialize Firebase Admin SDK with the service account key info dictionary
firebase_cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(firebase_cred)

db = firestore.client()




ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'JPG', 'JPEG'}

#Specify your own project details from Google Cloud
g_project_name = ''
g_project_id = ''
g_bucket_name = ''

g_datastore_query_by_kind = ''

## ------------------------------------------------------------      

class ImageMetadata:
    """
    Use this class to create am image file's metadata for insertion in the Cloud Datastore

    Multiple ctor's in Python: 

        1. https://www.geeksforgeeks.org/what-is-a-clean-pythonic-way-to-have-multiple-constructors-in-python/
    
        2. https://realpython.com/python-multiple-constructors/#:~:text=Using%20the%20%40classmethod%20decorator%20to,to%20provide%20multiple%20alternative%20constructors.

    """  

    def __init__(self, file, owner, location,size,created,updated):
        self._filename = secure_filename(file.filename)
        self._id = uuid.uuid4()
        self._owner = owner
        self._location = location
        self._size =round(size / 1024,1)
        self._created=created
        self._updated=updated
        self._createDate = self._created

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
    #metadata in FIREstore
    def upload_to_datastore(self):
        try:
            # Create a new document with a unique ID
            doc_ref = db.collection(u'images').document()
            
            doc_ref.set({
                "filename": self._filename,
                "owner": self._owner,
                "location": self._location,
                "size": f"{self._size} KB",
                "createDate": self._createDate
            })
            # Now you can return the document ID
            return doc_ref.id
        except Exception as e:
            print(f"An error occurred while uploading to Firestore: {e}")
            return None


## ------------------------------------------------------------     

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

## ------------------------------------------------------------ 

@app.route('/')
@app.route('/index')
def index():
    is_logged_in=session.get('logged_in',False)

    file_link_tuple=[]
    if is_logged_in:
        user_id=session.get('user_id')
        print("in index: ",session) 
        #retrieve only images for logged in user from firestore
        file_link_tuple = get_images_for_user(user_id)
        print("in index, file_link_tuple: ", file_link_tuple)
    # Check if user is authenticated and pass that status to the template
    return render_template('index.html', file_link_tuple=file_link_tuple, isLoggedIn=is_logged_in)

def parse_date(date_string):
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%b %d, %Y, %I:%M:%S %p", "%Y-%m-%d %I:%M:%S %p"):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse the date: {date_string}")

def get_images_for_user(user_id):
    # Firestore query to get images where 'owner' field is the user_id
    images_ref = db.collection(u'images').where(u'owner', u'==', user_id)
    try:
        # Execute the query
        images_docs = images_ref.stream()
        # Extract data from documents
        images_data = []
        for img_doc in images_docs:
            img_data = img_doc.to_dict()
            gs_path = f"gs://{g_bucket_name}/user_images/{img_data['owner']}/{img_data['filename']}"  # Correct gs_path
            create_date = parse_date(img_data['createDate']).strftime("%b %d, %Y, %I:%M:%S %p")
            images_data.append({
                'url': img_data['location'],  # URL to access the image, if needed for <img> tags
                'location': gs_path,  # File path using gs:// format
                'name': img_data['filename'],
                'size': f"{img_data['size']} KB" if isinstance(img_data['size'], int) else img_data['size'],
                'createDate': create_date,
                # Add any other image metadata you want to include
            })
        return images_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


from firebase_admin import auth

@app.route('/verify_token', methods=['POST'])
def verify_token():
    # Extract the token from the request.
    token = request.json.get('token')
    # Verify the token with Firebase Admin SDK.
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        # Now set the UID in the session.
        session['user_id'] = uid
        session['logged_in']=True
        return jsonify({'success': True}), 200
    except auth.InvalidIdTokenError:
        return jsonify({'success': False}), 401


@app.route('/login', methods=['POST'])
def login():
    uid = request.form.get('uid')
    email = request.form.get('email')
    # create a user session
    session['user_id'] = uid
    session['email'] = email
    session['logged_in'] = True 
    print("in login sesion:",session) 
    return jsonify({'success': True}), 200

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    session['logged_in'] = False  # User is now logged out
    return redirect(url_form('login'))


from flask import request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from firebase_admin import storage

# Ensure you have the right bucket name set up
bucket = storage.bucket('')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        flash('User is not logged in.')
        return redirect(url_for('login'))
    # Check if the post request has the file part
    if 'file_select_form' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file_select_form']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        user_id=session['user_id']
        print('in upload route,logged in, user_id: ',user_id)
        filename = secure_filename(file.filename)
        #capture filesize here 
        file.seek(0,os.SEEK_END) #go to EOF
        file_size=file.tell()
        print('File size in bytes:', file_size) 
        file.seek(0) #reset point to the start
        blob = bucket.blob(f'user_images/{user_id}/{filename}')
        blob.upload_from_string(file.read(), content_type=file.content_type)
        blob.make_public()
        public_url=blob.public_url
        #create and save image metadata
        created_date = datetime.utcnow().strftime("%b %d, %Y, %I:%M:%S %p")
        image_metadata = ImageMetadata(
            file,  # Assuming 'file' is the file object from the form
            user_id,
            public_url,
            file_size,  # This should be just the size without calling file.tell() again
            created_date,
            created_date
        )
        
        doc_id = image_metadata.upload_to_datastore()
        if doc_id:
            flash('Image uploaded and metadata saved.')
        else:
            flash('Failed to save image metadata.')
        
        return redirect(url_for('index'))
    
    return redirect(request.url)

@app.route('/user_images')
def user_images():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if the user isn't logged in

    # Query Firestore for images belonging to the user
    images = get_images_for_user(user_id)

    # Render a template, passing in the image URLs
    return render_template('user_images.html', images=images)

@app.route('/get_user_images')
def get_user_images():
    user_id = session.get('user_id')
    if user_id:
        images_data = get_images_for_user(user_id)  # This should return a list of image data dictionaries
        return jsonify(images_data)
    else:
        return jsonify([]), 401

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

 
@app.route('/delete_image', methods=['POST'])
def delete_image():
    try:
        # Parse JSON data from the request
        data = request.get_json()
        print('received data:',data)
        image_url = data['imagePath']
        image_name = data['imageName']
        print(f"Received image URL: {image_url}")
        print(f"Received image name: {image_name}")
        # The image path within the bucket is obtained by removing the domain part of the URL
        url_parts = image_url.split('/')
        bucket_index = url_parts.index('')  # Find the index of the bucket name
        path_within_bucket = '/'.join(url_parts[bucket_index + 1:])  # Join the remaining parts to get the path
        print(f"path_within_bucket: {path_within_bucket}")
        #Initialize the storage bucket
        bucket = storage.bucket('')
        
        # Initialize a blob representing the file to delete
        blob = bucket.blob(path_within_bucket)
        
        # Delete the blob (file) from Firebase Storage
        blob.delete()
        
        # Initialize Firestore client
        db = firestore.client()
        
        # Query Firestore for the document with matching filename to delete metadata
        image_metadata_ref = db.collection('images').where('filename', '==', image_name).stream()

        # Delete each document found with the matching filename
        for doc in image_metadata_ref:
            doc.reference.delete()

        # Return success message
        return jsonify({'success': True, 'message': 'Image and metadata deleted successfully'})
    except Exception as e:
        # If an error occurs, print it to the console and return an error message
        print("Error in /delete_image route:", e)
        return jsonify({'success': False, 'message': str(e)}), 500


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
