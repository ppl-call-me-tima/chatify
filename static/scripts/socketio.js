function updateSendButton() {
    const messageInputElement = document.getElementById("message");
    const sendButtonElement = document.getElementById("send-button");

    if (messageInputElement.value === "") {
        sendButtonElement.disabled = true;
    } else {
        sendButtonElement.disabled = false;
    }
}

var socketio = io();

socketio.on("load_messages", (rows) => {
    for (const row of rows) {
        loadSingleMessageIntoMessageBox(row);
    }
});

socketio.on("message", (data) => {
    loadSingleMessageIntoMessageBox(data);
});

const joinRoom = (friendship_id, username) => {
    document.getElementById("message-box").innerHTML = "";
    socketio.emit("join_a_room", friendship_id);
    document.getElementById("message").disabled = false;
    document.getElementById("message").focus();
    document.getElementById("message-box-header-name").textContent = username;
}

const sendMessage = () => {
    const message = document.getElementById("message").value;
    const username = document.getElementById("message-box-header-name").textContent;

    socketio.emit("message", {
        msg_to: username,
        message: message
    });
    document.getElementById("message").value = "";
    document.getElementById("send-button").disabled = true;
}

// HELPER FUNCTIONS
function loadSingleMessageIntoMessageBox(data) {
    const messageBoxElement = document.getElementById("message-box");
    const messageDivElement = document.createElement("div");
    messageDivElement.innerHTML = `
        <strong>${data["msg_from_username"]}</strong> : ${data["msg"]} <span style="font-size: 7.5px;">${data["timestamp"]}</span>
    `;
    messageBoxElement.appendChild(messageDivElement);
}