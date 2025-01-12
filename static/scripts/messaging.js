var currentOpenedChatId = "";

document.getElementById("message").addEventListener("keydown", (event) => {
    if (event.code == "Enter" && document.getElementById("message").value.trim().length !== 0) {
        sendMessage();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.code == "Escape") {
        resetMessageBox();
    }
});

function resetMessageBox() {
    if (currentOpenedChatId.length !== 0) {
        document.getElementById(`chat-card-${currentOpenedChatId}`).style.backgroundColor = "white";
        currentOpenedChatId = "";
    }

    document.getElementById("message").value = "";
    document.getElementById("message").disabled = true;
    document.getElementById("send-button").disabled = true;

    document.getElementById("message-box-header").style.borderBottom = "none";
    document.getElementById("message-box-header").innerHTML = `<br>`;


    document.getElementById("message-box-outer").innerHTML = `
        <div id="message-box">
            <div id="default-box">
                <span id="default-message-box-display" class="geist-mono-400">
                    SELECT A FRIEND TO START CHATTING
                </span>
            </div>
        </div>
    `;
}

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

socketio.on("profanity_detected", (data) => {
    document.getElementById("profanity-warning-box").classList.toggle("show");
});

function profanityOkay(){
    document.getElementById("profanity-warning-box").classList.toggle("show");
}

const joinRoom = (friend_id, username) => {
    socketio.emit("join_a_room", parseInt(friend_id));

    if (currentOpenedChatId.length !== 0) {
        document.getElementById(`chat-card-${currentOpenedChatId}`).style.backgroundColor = "white";
    }

    currentOpenedChatId = friend_id;

    document.getElementById(`chat-card-${currentOpenedChatId}`).style.backgroundColor = "rgb(230, 230, 230)";
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
    messageDivElement.classList.add("message");
    messageDivElement.classList.add("mb-1");

    messageDivElement.innerHTML = `
        ${data["msg"]} <span style="font-size: 0.75rem;"><sub><em>${data["timestamp"]}</em></sub></span>
    `;

    if (data["msg_from_username"] === document.getElementById("message-box-header-name").innerText) {
        messageDivElement.classList.add("received-message");
    }
    else {
        messageDivElement.classList.add("sent-message");
    }

    messageBoxElement.appendChild(messageDivElement);
}