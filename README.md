# MultiMedia_group24
This repository will include all of the code required to get sentiment levels from TikTok videos and how to build the classification model.

## Directories
TikTokPy-main includes the TikTok API code we used. Its instruction can be found in the corresponding readme.
- Load a list of video URLs
- Run the python script
- The videos can be found under videos/video_id
Py-Feat
- Transform the videos into separate frames
- Run a facial recognition model on the frames to compute the emotions
Classification
- Load all of the features extracted from the different models
- Run classification algorithms and compare the results by looking at the confusion matrix. 

## Conda Environment
The `requirements.txt` file includes all of the required Python modules to be able to run the TikTok API main script.