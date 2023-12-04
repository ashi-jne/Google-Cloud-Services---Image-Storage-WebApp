# Google Cloud Services - Image Sotrage Web App

Cloud Computing



**Project Description and Objectives**
In this project we have created an image hosting site that can split traffic, run as a serverless app with user accounts and authentication facilitated through Continuous Integration - Continuous Deployment (CI/CD) on Google Cloud. 

The object of this project is to demonstrate:
- user authentication and separate user accounts for image storage on the app using Firebase
- store the image and image’s metadata in the cloud using Firestore Database and Firebase Storage
- allow users to view their respective images and image metadata on the app
- allow users to delete pictures they have uploaded 
- automatic application scaling for increased traffic
- security from outside access to different parts of the layers


As a whole this app will allow you to use one of the two live versions to login to your account, upload, view, and delete your own images. 


Implementation Details

- Configured Cloud Code Repository (called “ProjectTest” in this example) with all the files contained in this repository.
- Configured Firebase Storage, Database, and Authentication for file storage, metadata data storage, and user authentication. 
- Created a new service in Cloud Run using the “Continuously deploy new revisions from a source repository” option using the repository mentioned above with the Dockerfile build type.
- Compiled a backend for the web application called “project.py” with calls to all the Google APIs used in the application and configured HTTPS requests to be used by the frontend file “index. html”, which allows users to invoke these HTTPS requests through button clicks and page loads. The frontend was modified significantly to add popup modals for Login and Signup, and buttons for Logout, and Delete Image. 
- Opened the Cloud Repository for the app and made changes and commit+pushed to the main branch after testing it out on the cloud emulator. (Several changes were made during this phase of the project including the setup of firebase authentication, storage, firestore in native mode, and front end modifications like background colors, additional buttons, and forms. 
- The push to main triggered a build and a new revision was created for the service which is tagged “bluebg” in Cloud Run to distinguish between 2 live verions
- Reopened the Cloud Repository and committed and pushed changes to turn the app background green. The push triggered a new build on the same service and this version went live. (This version is tagged “greenbg”).
- From the service configured the traffic split using the “Manage Traffic” to split the traffic 50-50 between the “bluebg” version  and “greenbg” version. 

When the app is accessed through the service URL, half the time the blue version will load, the other half will be the green version. Both versions have otherwise identical builds and backend. 



index.html: contains the frontend for the app
project.py: contains the backend code for the app with integrations to the various APIs used
Dockerfile: specifies containerizing parameters for the app
cloudbuild.yaml: specifies parameters for the automated deployment of the app




Google Secret Manager: used for storing API keys and user session information for this app. 
Firebase Authentication: used for creating user accounts and authentication access through an email and password database
Firebase Storage: used for storing user images in their respective folders (differentiated by user_id)
Firestore Database: used to store the metadata of each uploaded image along with its associated user_id
Google Cloud Repositories: contains the main frontend (index.html) and backend(project.py) files for the app, both files call on the Google and Firebase APIs within
HTTPS Requests: requests that carry out functions in the backend using the APIs when called on from the frontend


**Design Decisions**

Secret Manager: used this component to store both Firebase Service Account information and the SECRET_KEY used by Flask to securely sign the session cookie. 
Firebase Config: obtained these key-value pairs from the Firebase console. Per the Firebase documentation, it is safe to include this information in the source code, as it cannot be used by malicious actors to compromise the application data.
Firebase Rules for File Security:

service firebase.storage {
  match /b/{bucket}/o {
    // Match any file in the /users/{userId}/ path
    match /users/{userId}/{allPaths=**} {
      // Allow read/write if the userId in the path matches the authenticated user's UID
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}

General security of the application: The Firebase config stored inside of the Secret Manager is used to initialize the Firebase Admin SDK within the application. This config contains necessary credentials for the backend to communicate security with Firebase services. That is, it authenticates your application’s backend with Firebase. It is also important to note that the session key is used to maintain the state between the server (backend) and client (frontend) across multiple requests. When a user logs into a web application, the server creates a session to keep track of the user’s state, and a session key (here is an easily recognizable constant string) is used to reference this session. 
Firebase Storage Schema:


/{bucket-name}
	/{user-uploads}
                	photo1.jpg:
                	photo2.jpg
 		…
/{metadata} 
{createDate: “timestamp” ,filename: “name of file” ,location: “path of file”,owner: “userId”,size: “in KB”} 
	
Firestore Database in Native Mode (for metadata) Object Organization: Firestore in Native Mode uses a document-collection model, where data is stored in documents, and these documents are organized into collections. This offers real time synchronization and updates. As a user deletes or uploads images the database deletes and uploads in realtime without needing to refresh or restart the page. Native Mode is built to automatically scale effortlessly and handle varying loads while maintaining performance. It is important to note the main reason for using Firestore in Native Mode is that it is designed to have better integration with Firebase services.Firestore Database in Native Mode also has offline support, which works well even with intermittent internet connections. 


Areas for Development/Lessons Learned:
The secret key for firebase authentication is stored safely inside of the Secret Manager. However, the sessions manager key is hardcoded inside of the .py file for ease of use across a group of students working on the same project as it doesn’t require any additional steps to fetch the keys from an external source. The security risks are apparent especially if the source code becomes public, or if the secret key is embedded in the source code and the code is transmitted over insecure channels (i.e. pushing code to a remote repository over an unencrypted channel), which contains potential for a Man in the Middle Attack, especially given that our secret key is a sentence and not a string of random characters. 
(NOTE: Application Instructions section on the next page)

Application Instructions: 

- Access the Application: Open a web browser and navigate to the service URL 
- Login to the application:
enter your email and password
click “Login”
![image](https://github.com/ashi-jne/Project3-Group17/assets/96357892/a40cb063-e873-4fe3-86bd-8961d0403aae)

- Sign-up on the application:
click the link at the bottom of the Login popup saying “Sign up”
enter your email and password for the account and click “Submit”
if you already have an account click the link on the bottom right of the popup saying “Login” to return to to the Log In popup

![image](https://github.com/ashi-jne/Project3-Group17/assets/96357892/a08cd7cf-e436-4460-968c-7b2d0bb52b91)


Upon successfully logging in or signing up you should see one of the two versions of the homepage of the application.
Blue:
![image](https://github.com/ashi-jne/Project3-Group17/assets/96357892/17f9cc75-5821-4c0d-985f-075a5e6ea132)


Green: 
![image](https://github.com/ashi-jne/Project3-Group17/assets/96357892/08e64fe1-587a-4a45-828a-d4a77cab31ce)




Upload Images:
Click the "Choose File" button.
Select an image file from your local machine.
Click "Submit" to upload the image.
Visualize Images:
Uploaded images are displayed on the home page.
Click on an image to view it in a modal pop-up in detail with its metadata.
Exit the pop-up by clicking on the ‘x’ or Close button. 

![image](https://github.com/ashi-jne/Project3-Group17/assets/96357892/799971d0-6cc0-430e-b5cf-c714e8bf45fd)


Delete Images:
Select an image from the home page to display detail
Click the “Delete Image” button

Download Images:
On desktop/laptop devices, right-click on the image in the visualization pop-up and select “Save as…” to download the image.
On a mobile device, simply use the device’s screen-capture feature to save a displayed image.
Log-out of application:
Exit the image visualization pop-up
Click the “Logout” button on the bottom left of the home page
![image](https://github.com/ashi-jne/Project3-Group17/assets/96357892/146712cb-08e3-462c-b745-04cd49a176c0)




