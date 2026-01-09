const socket = io();

const chatData = document.getElementById("chatData");
const myId = chatData.dataset.myid;
const targetId = chatData.dataset.targetid;

const room = myId < targetId
    ? `${myId}_${targetId}`
    : `${targetId}_${myId}`;

socket.emit("join", { room });

const sendBtn = document.getElementById("sendBtn");
const input = document.getElementById("messageInput");
const chatArea = document.getElementById("chatArea");

sendBtn.onclick = () => {
    const msg = input.value.trim();
    if (!msg) return;

    socket.emit("send_message", {
        room: room,
        message: msg,
        sender: myId,
        receiver: targetId
    });

    input.value = "";
};

input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
        sendBtn.click();
    }
});

socket.on("receive_message", data => {
    const div = document.createElement("div");
    div.className = data.sender == myId ? "bubble me" : "bubble you";
    div.innerText = data.message;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
});
