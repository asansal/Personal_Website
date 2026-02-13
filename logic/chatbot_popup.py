"""
Chatbot Popup Component for Streamlit
Componente de chatbot flotante profesional
"""

import streamlit as st
import streamlit.components.v1 as components

def inject_chatbot_popup():
    """
    Inyecta el HTML/CSS/JS para un chatbot popup flotante
    """
    popup_code = """
    <style>
    /* Botón flotante del chatbot */
    .chatbot-trigger {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #4CAF50, #45a049);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 
            0 4px 20px rgba(76, 175, 80, 0.4),
            0 0 30px rgba(76, 175, 80, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 9999;
        border: 3px solid rgba(255, 255, 255, 0.2);
        animation: pulse-glow 3s ease-in-out infinite;
    }
    
    .chatbot-trigger:hover {
        transform: scale(1.1) translateY(-2px);
        box-shadow: 
            0 6px 30px rgba(76, 175, 80, 0.6),
            0 0 40px rgba(76, 175, 80, 0.3);
    }
    
    .chatbot-trigger svg {
        width: 30px;
        height: 30px;
        fill: white;
    }
    
    @keyframes pulse-glow {
        0%, 100% {
            box-shadow: 
                0 4px 20px rgba(76, 175, 80, 0.4),
                0 0 30px rgba(76, 175, 80, 0.2);
        }
        50% {
            box-shadow: 
                0 4px 25px rgba(76, 175, 80, 0.6),
                0 0 40px rgba(76, 175, 80, 0.4);
        }
    }
    
    /* Badge de notificación */
    .chatbot-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        width: 20px;
        height: 20px;
        background: #ff4444;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        color: white;
        font-weight: bold;
        border: 2px solid #0a0e27;
        animation: bounce 2s ease infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    /* Ventana del chatbot */
    .chatbot-popup {
        position: fixed;
        bottom: 100px;
        right: 30px;
        width: 380px;
        height: 550px;
        background: linear-gradient(180deg, 
            rgba(10, 14, 39, 0.98) 0%, 
            rgba(22, 33, 62, 0.96) 100%
        );
        border-radius: 20px;
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.5),
            0 0 40px rgba(76, 175, 80, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(76, 175, 80, 0.3);
        display: none;
        flex-direction: column;
        overflow: hidden;
        z-index: 9998;
        animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .chatbot-popup.active {
        display: flex;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    /* Header del chatbot */
    .chatbot-header {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        padding: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .chatbot-header h3 {
        color: white;
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .chatbot-header .status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.9);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #66FF66;
        border-radius: 50%;
        animation: pulse-dot 2s ease infinite;
        box-shadow: 0 0 10px #66FF66;
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .close-btn {
        background: rgba(255, 255, 255, 0.2);
        border: none;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        font-size: 18px;
        font-weight: bold;
    }
    
    .close-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: rotate(90deg);
    }
    
    /* Cuerpo del chatbot */
    .chatbot-body {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    
    .chatbot-body::-webkit-scrollbar {
        width: 6px;
    }
    
    .chatbot-body::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
    }
    
    .chatbot-body::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #4CAF50, #45a049);
        border-radius: 3px;
    }
    
    /* Mensaje del chat */
    .chat-message {
        display: flex;
        gap: 10px;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message.bot {
        align-self: flex-start;
    }
    
    .chat-message.user {
        align-self: flex-end;
        flex-direction: row-reverse;
    }
    
    .message-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .bot .message-avatar {
        background: linear-gradient(135deg, #4CAF50, #45a049);
    }
    
    .user .message-avatar {
        background: linear-gradient(135deg, #0066cc, #0052a3);
    }
    
    .message-bubble {
        background: rgba(255, 255, 255, 0.08);
        padding: 12px 16px;
        border-radius: 16px;
        max-width: 75%;
        color: rgba(255, 255, 255, 0.95);
        font-size: 0.95rem;
        line-height: 1.5;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .user .message-bubble {
        background: linear-gradient(135deg, #0066cc, #0052a3);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* Mensaje de bienvenida */
    .welcome-message {
        text-align: center;
        padding: 20px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
    }
    
    .welcome-message h4 {
        color: #4CAF50;
        margin-bottom: 10px;
        font-size: 1.1rem;
    }
    
    /* Sugerencias rápidas */
    .quick-suggestions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 0 20px 15px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .suggestion-chip {
        background: rgba(76, 175, 80, 0.15);
        color: #66BB6A;
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    
    .suggestion-chip:hover {
        background: rgba(76, 175, 80, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
    }
    
    /* Footer del chatbot */
    .chatbot-footer {
        padding: 15px 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(0, 0, 0, 0.2);
    }
    
    .input-container {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    #chatbot-input {
        flex: 1;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 12px;
        padding: 12px 16px;
        color: white;
        font-size: 0.95rem;
        outline: none;
        transition: all 0.3s ease;
    }
    
    #chatbot-input:focus {
        background: rgba(255, 255, 255, 0.12);
        border-color: #4CAF50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.2);
    }
    
    #chatbot-input::placeholder {
        color: rgba(255, 255, 255, 0.4);
    }
    
    .send-btn {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        border: none;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    
    .send-btn:hover {
        transform: scale(1.1) rotate(15deg);
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
    }
    
    .send-btn svg {
        width: 20px;
        height: 20px;
        fill: white;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        gap: 4px;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        width: fit-content;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #4CAF50;
        border-radius: 50%;
        animation: typing 1.4s ease infinite;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
        30% { transform: translateY(-10px); opacity: 1; }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .chatbot-popup {
            width: calc(100vw - 40px);
            height: calc(100vh - 150px);
            bottom: 20px;
            right: 20px;
        }
        
        .chatbot-trigger {
            bottom: 20px;
            right: 20px;
        }
    }
    </style>
    
    <!-- Botón flotante -->
    <div class="chatbot-trigger" id="chatbotTrigger">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3 .97 4.29L2 22l5.71-.97C9 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.38 0-2.68-.33-3.83-.91L4 20l.91-4.17C4.33 14.68 4 13.38 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8zm-4-8h2v2H8v-2zm4 0h2v2h-2v-2zm4 0h2v2h-2v-2z"/>
        </svg>
        <div class="chatbot-badge">💬</div>
    </div>
    
    <!-- Ventana del chatbot -->
    <div class="chatbot-popup" id="chatbotPopup">
        <div class="chatbot-header">
            <div>
                <h3>🤖 AI Assistant</h3>
                <div class="status">
                    <div class="status-dot"></div>
                    <span>Online</span>
                </div>
            </div>
            <button class="close-btn" id="closeChat">×</button>
        </div>
        
        <div class="quick-suggestions">
            <div class="suggestion-chip" onclick="sendSuggestion('¿Cuál es tu experiencia en Data Science?')">
                💼 Experiencia
            </div>
            <div class="suggestion-chip" onclick="sendSuggestion('¿Qué tecnologías dominas?')">
                🛠️ Skills
            </div>
            <div class="suggestion-chip" onclick="sendSuggestion('Cuéntame sobre tus proyectos')">
                🚀 Proyectos
            </div>
        </div>
        
        <div class="chatbot-body" id="chatbotBody">
            <div class="welcome-message">
                <h4>👋 ¡Hola! Soy tu asistente virtual</h4>
                <p>Pregúntame sobre la experiencia, habilidades y proyectos de Alejandro en Data Science, IA y Bioinformática.</p>
            </div>
        </div>
        
        <div class="chatbot-footer">
            <div class="input-container">
                <input 
                    type="text" 
                    id="chatbot-input" 
                    placeholder="Escribe tu pregunta..."
                    onkeypress="handleEnter(event)"
                />
                <button class="send-btn" onclick="sendMessage()">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
    
    <script>
    // Toggle chatbot popup
    document.getElementById('chatbotTrigger').addEventListener('click', function() {
        const popup = document.getElementById('chatbotPopup');
        popup.classList.toggle('active');
        
        // Remove badge when opened
        const badge = document.querySelector('.chatbot-badge');
        if (popup.classList.contains('active') && badge) {
            badge.style.display = 'none';
        }
    });
    
    document.getElementById('closeChat').addEventListener('click', function() {
        document.getElementById('chatbotPopup').classList.remove('active');
    });
    
    function sendSuggestion(text) {
        document.getElementById('chatbot-input').value = text;
        sendMessage();
    }
    
    function handleEnter(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    }
    
    function sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (message === '') return;
        
        // Add user message
        addMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send to Streamlit (this will trigger the chatbot logic)
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: message
        }, '*');
        
        // Simulate response (in real implementation, this comes from Streamlit)
        setTimeout(() => {
            hideTypingIndicator();
            // Response will be handled by Streamlit callback
        }, 1000);
    }
    
    function addMessage(text, type) {
        const chatBody = document.getElementById('chatbotBody');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'bot' ? '🤖' : '👤';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = text;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        chatBody.appendChild(messageDiv);
        
        // Scroll to bottom
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    let typingElement = null;
    
    function showTypingIndicator() {
        const chatBody = document.getElementById('chatbotBody');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot';
        messageDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(typingDiv);
        chatBody.appendChild(messageDiv);
        typingElement = messageDiv;
        
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    function hideTypingIndicator() {
        if (typingElement) {
            typingElement.remove();
            typingElement = null;
        }
    }
    
    // Listen for responses from Streamlit
    window.addEventListener('message', function(event) {
        if (event.data.type === 'chatbot-response') {
            hideTypingIndicator();
            addMessage(event.data.message, 'bot');
        }
    });
    </script>
    """
    
    # Inyectar el código HTML
    components.html(popup_code, height=0)


def get_chatbot_message():
    """
    Obtiene mensajes del chatbot popup
    Retorna el mensaje del usuario o None
    """
    # Este componente escucha los mensajes enviados desde el popup
    message = components.html("""
        <script>
        window.addEventListener('message', function(event) {
            if (event.data.value) {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: event.data.value
                }, '*');
            }
        });
        </script>
    """, height=0)
    
    return message


def send_chatbot_response(message):
    """
    Envía una respuesta al chatbot popup
    """
    components.html(f"""
        <script>
        window.parent.postMessage({{
            type: 'chatbot-response',
            message: '{message}'
        }}, '*');
        </script>
    """, height=0)