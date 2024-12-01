var socketio = io();

socketio.on("load_messages", (rows) => {
    for (const row of rows){
        console.log(row);

        const messageBoxElement = document.getElementById("message-box")
        const messageDivElement = document.createElement("div");
        messageDivElement.innerHTML += `
            <strong>${row["msg_from_username"]}</strong> : ${row["msg"]} - ${row["timestamp"]}
        `;
        messageBoxElement.appendChild(messageDivElement);
    }
});

socketio.on("message", (message) => {
    const messageBoxElement = document.getElementById("message-box");
    const messageDivElement = document.createElement("div");
    messageDivElement.textContent = message;
    messageBoxElement.appendChild(messageDivElement);
});

const joinRoom = (friendship_id, username) => {
    console.log(friendship_id);
    document.getElementById("message-box").innerHTML = "";
    socketio.emit("join_a_room", friendship_id);
    document.getElementById("message").disabled = false;
    document.getElementById("message").focus();
    document.getElementById("send-button").disabled = false;
    document.getElementById("message-box-header-name").textContent = username;
    socketio.emit("load_messages");
}

const sendMessage = () => {
    const message = document.getElementById("message").value;
    const username = document.getElementById("message-box-header-name").textContent;
    console.log(message);

    socketio.emit("message", {
        msg_to: username,
        message: message
    });
    document.getElementById("message").value = "";
}