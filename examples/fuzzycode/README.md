# FuzzyCode Problem Solutions

## Key Files and What They Solve:

### 1. **fuzzycode_debug_form_validation.py**
- **Problem**: Sign In button stayed disabled despite fields appearing filled
- **Discovery**: Hidden required fields were blocking form validation
- **Solution**: Debug all inputs with form.checkValidity() to find issues

### 2. **fuzzycode_debug_iframe.py**
- **Problem**: Couldn't access login form in iframe
- **Discovery**: There were 11 input fields total, not just 2 visible ones
- **Solution**: Use direct array access - inputs[0] for username, inputs[1] for password
- **Key Learning**: Same-origin iframes ARE accessible with iframe.contentDocument
- **Test Credentials**: 
  - Username: `robert.norbeau+test2@gmail.com`
  - Password: `robert.norbeau+test2`

### 3. **fuzzycode_close_modal_reload.py**
- **Problem**: Welcome modal wouldn't close after successful login
- **Solution**: Reload the page - session persists through cookies
- **Trade-off**: May need to re-establish some client-side state

### 4. **fuzzycode_fill_login_better.py** (if found)
- **Problem**: Complex selectors failing to find form fields
- **Solution**: Use simpler, more robust selection methods

## Key Patterns Learned:

1. **Direct Array Access**: When selectors fail, use `inputs[0]`, `inputs[1]`
2. **Form Validation**: ALL required fields must be filled, even hidden ones
3. **Modal Handling**: Sometimes reload is the simplest solution
4. **Debugging**: Console logs reveal hidden errors (401 auth required)