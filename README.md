# 🚀 Extract information from CV using LLM

### This app provides boilerplate code to turn information from a CV into structured JSON using an LLM:
👉 The following process is performed by this code, step by step:
- Takes as input a CV. The CV can be in PNG, JPG, or PDF format
- Reads the prompt.txt file that contains your prompt and the JSON format the LLM should respond with
- The CV data is then read from the file (rb) and uploaded to Azure Storage
- A user generated SAS token is created for this file that was just uploaded
- This SAS token is passed to Azure Vision where OCR is performed on this file. "Normal" PDFs, i.e. PDFs that contain text, will also be handled.
- The returned OCR data is then passed to langchain to chunk (not really necessary, but providing the code as part of the solution)
- Each chunk (well, just one), is then passed to an Azure OpenAI instance together with the prompt
- Finally, the JSON object received from Azure OpenAI is written to a file in the cv_details_output folder

This extracted information can be used further downstream, e.g. to prepopulate your job portal once a user uploaded their CV, or present it on an internal HR/recruitment portal, etc


### Prompt file
🖹 Create the prompt in "prompt.txt" in the root of this app. An example prompt is included in the repo


### Environment variables
🔡 Environment variables can be defined for pretty much everything. See the example environment variable file in the repo


### Logging
📣 The app includes some basic logging using Python's built-in logger functionality
