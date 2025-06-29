# Steps Document

## Project specific configuration
- Username: "robert.norbeau+test2@gmail.com"
- Password: "robert.norbeau+test2"

## Format
- This is just an instruction guide to claude code, claude code can use it to do the steps manuall

## Steps
### 1
- Navigate to https://Fuzzycode.dev
- Wait till it's loaded
- Take a screenshot
- Look at screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it
### 2
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the profile picture to click to login
- Use the deeepelement search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 3
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the username field to click
- Use the deep element search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 4
- Type the username text "robert.norbeau+test2@gmail.com"
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 5
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the password field to click
- Use the deep element search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 6
- Type the password text "robert.norbeau+test2"
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 7
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the sign in button to click
- Use the deep element search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 8
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the X button to close modal
- Use the deep element search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 9
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the request text area to click inside
- Use the deep element search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 10
- Type "Write a Python function to check if a number is prime" into request area
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 11
- Analyze the screenshot with gemini and have it give the bounding boxes and draw them
- Look at them and find the "Fuzzy Code It" button to click
- Use the deep element search to find the elements in that position
- If one of the elements makes sense plan to click on it (if none are good tell the user and explain root cause if you can)
- Get the crosshair screenshot, verify it makes sense
- Send the click
- Wait
- Take a screenshot
- Look at the screenshot
- Verify it is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

### 12
- Wait for page to process (may take several seconds)
- Take a screenshot
- Look at the screenshot
- Check if still loading (look for loading indicators)
- If loading, wait more and take another screenshot
- If error message appears, alert user of the error and provide details
- If result appears below that looks like it's an attempt to implement the python function as an html webapp inside of the response iframe, claim success
- Verify final state is good or tell the user of the issue, and if you can find the root cause for it and ask how to handle it

## Steps (Short notation)
1. Navigate(https://Fuzzycode.dev)
2. Action("Click on the user profile to open the login screen") [prefer:screenshot_bb_deep_element_method]
3. Action("Click on the username field") [prefer:screenshot_bb_deep_element_method]
4. Action("Type username text") [prefer:page.type]
5. Action("Click on the password field") [prefer:screenshot_bb_deep_element_method]
6. Action("Type password text") [prefer:page.type]
7. Action("Click sign in button") [prefer:screenshot_bb_deep_element_method]
8. Action("Click X button to close modal") [prefer:screenshot_bb_deep_element_method]
9. Action("Click inside request text area to type request") [prefer:screenshot_bb_deep_element_method]
10. Action("Type 'Write a Python function to check if a number is prime' into request area") [prefer:page.type]
11. Action("Fuzzy Code It button") [prefer:screenshot_bb_deep_element_method]
12. DetermineSuccess("Wait if loading, alert user if there is an error preventing, claim success if result comes back below that looks like it's an attempt to implement the python function as an html webapp inside of the response iframe")

## Hard rules
- You always look at screenshots yourself, not programmatically
- Always before clicking take a crosshair screenshot as well