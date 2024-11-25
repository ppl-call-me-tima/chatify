function inlineEdit(originalNameID, editButtonID) {
    const originalNameElement = document.getElementById(originalNameID);
    const editButtonElement = document.getElementById(editButtonID);
    const originalName = originalNameElement.textContent;

    const inputField = document.createElement("input");
    const saveButton = document.createElement("button");

    inputField.value = originalName;
    inputField.classList = "h1";
    inputField.style.width = "340px";

    saveButton.textContent = "Change";

    originalNameElement.parentNode.insertBefore(inputField, originalNameElement);
    editButtonElement.parentNode.insertBefore(saveButton, editButtonElement);

    originalNameElement.style.display = "none";
    editButtonElement.style.display = "none";


    saveButton.onclick = async function () {
        const newName = inputField.value;
        inputField.remove();
        saveButton.remove();

        const response = await fetch("/profile/inline_edit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: newName
            })
        });          
        originalNameElement.textContent = newName;

        originalNameElement.style.display = "inline";
        editButtonElement.style.display = "inline";
    }
}