function inlineEdit(originalDisplayID) {
    const originalDisplayElement = document.getElementById(originalDisplayID);

    console.log(originalDisplayElement.textContent, originalDisplayElement.textContent.length);

    if (originalDisplayElement.textContent === "Tell people about yourself..." || 
        originalDisplayElement.textContent === "Add your name"
    ){
        originalDisplayElement.textContent = "";
    }

    const editButtonElement = document.getElementById(originalDisplayID + '-edit-button');
    const originalDisplayContent = originalDisplayElement.textContent;

    const inputField = document.createElement("input");
    const saveButton = document.createElement("button");
    const tickImageElement = document.createElement("img");
    tickImageElement.src = "../static/icons/tick.png";
    saveButton.appendChild(tickImageElement);

    inputField.value = originalDisplayContent;
    saveButton.classList = "btn p-0";

    switch(originalDisplayID){
        case "name":
            inputField.classList = "h1";
            inputField.style.width = "340px";
            tickImageElement.style.height = "25px";
            break;

        case "bio":
            inputField.classList = "h6";
            inputField.style.width = "300px";
            tickImageElement.style.height = "15px";
            break
    }

    originalDisplayElement.parentNode.insertBefore(inputField, originalDisplayElement);
    editButtonElement.parentNode.insertBefore(saveButton, editButtonElement);

    originalDisplayElement.style.display = "none";
    editButtonElement.style.display = "none";

    inputField.focus();

    saveButton.onclick = async function () {
        const newDisplayContent = inputField.value;
        inputField.remove();
        saveButton.remove();

        const response = await fetch("/profile/inline_edit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                field: originalDisplayID,
                value: newDisplayContent
            })
        });
        originalDisplayElement.textContent = newDisplayContent;

        originalDisplayElement.style.display = "inline";
        editButtonElement.style.display = "inline";
    }
}