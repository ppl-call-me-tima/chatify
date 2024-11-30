var socketio = io();

socketio.on("message", (message) => {
    const messageBoxElement = document.getElementById("message-box");
    const messageDivElement = document.createElement("div");
    messageDivElement.textContent = message;
    messageBoxElement.appendChild(messageDivElement);
});

const selectFriend = (friendship_id) => {
    console.log(friendship_id);
    socketio.emit("join_a_room", friendship_id);
    document.getElementById("message").disabled = false;
    document.getElementById("send-button").disabled = false;
}

const sendMessage = () => {
    const message = document.getElementById("message").value;
    console.log(message);

    socketio.emit("message", message);
    document.getElementById("message").value = "";
}