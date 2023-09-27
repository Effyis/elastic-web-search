function copyToClipboard(index) {
    const textarea = document.getElementById('json-' + index);
    textarea.style.display = "block";  // Temporarily display the textarea
    textarea.select();
    document.execCommand('copy');
    textarea.style.display = "none";  // Hide the textarea again
}