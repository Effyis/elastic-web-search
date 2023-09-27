function copyToClipboard(elementId) {
    var textArea = document.getElementById(elementId);
    textArea.select();
    document.execCommand('copy');
    alert('JSON copied to clipboard!');
}
