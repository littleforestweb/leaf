window.addEventListener('DOMContentLoaded', async function main() {

})

function sanitizeInput(event) {
    let enteredValue = event.target.value;
    let sanitizedValue = enteredValue.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    sanitizedValue = sanitizedValue.replace(/\xA0/g, '');
    event.target.value = sanitizedValue;
}

function sanitizePrintedInput() {
    let inputElement = document.getElementById('printedInput');
    let enteredValue = inputElement.value;
    let sanitizedValue = enteredValue.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    sanitizedValue = sanitizedValue.replace(/\xA0/g, '');
    inputElement.value = sanitizedValue;
}

function escapeHtml(unsafe) {
    return $('<div />').text(unsafe).html();
}

function logout() {
    // Remove JWT token from localStorage
    localStorage.removeItem('jwtToken');
}