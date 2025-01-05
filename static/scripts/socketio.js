document.getElementById("message").addEventListener("keydown", (event) => {
    if (event.code == "Enter"){
        sendMessage();
    }
});

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
    document.getElementById("message-box").innerHTML = "";
    document.getElementById("message-box").style.height = "auto";

    for (const row of rows) {
        loadSingleMessageIntoMessageBox(row);
    }
});

socketio.on("message", (data) => {
    loadSingleMessageIntoMessageBox(data);
});

const joinRoom = (friend_id, username) => {
    socketio.emit("join_a_room", parseInt(friend_id));
    document.getElementById("message").disabled = false;
    document.getElementById("message").focus();
    document.getElementById("message-box-header").style.borderBottom = "1px solid black";

    var anchor = document.createElement("a");
    anchor.id = "message-box-header-name";
    anchor.href = `/profile/${username}`;
    anchor.innerText = username;
    anchor.style.textDecoration = "none";
    anchor.style.color = "black";

    document.getElementById("message-box-header").innerHTML = "";
    document.getElementById("message-box-header").appendChild(anchor);
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