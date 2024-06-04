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

function escapeHtmlTags(str) {
  return str.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function unescapeHtml(html) {
  const text = document.createElement("textarea");
  text.innerHTML = html;
  return text.value;
}

function logout() {
    // Remove JWT token from localStorage
    localStorage.removeItem('jwtToken');
}