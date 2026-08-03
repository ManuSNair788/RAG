import re

def update_html():
    with open('static/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    # 1. Replace the chat container
    chat_container_pattern = re.compile(r'<!-- Chat History Container -->.*?<!-- Floating Input Area -->', re.DOTALL)
    new_chat_container = """<!-- Chat History Container -->
<div id="chat-container" class="flex-1 max-w-[800px] mx-auto w-full px-container-padding py-12 flex flex-col gap-8 relative z-10 overflow-y-auto pb-32">
    <!-- Assistant Message (Welcome) -->
    <div class="flex flex-col items-start gap-2 animate-in fade-in slide-in-from-left-4 duration-500">
        <div class="flex items-center gap-3 mb-1">
            <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">smart_toy</span>
            </div>
            <span class="text-label-md font-bold text-primary">AI Advisor</span>
        </div>
        <div class="bg-surface-container-low text-on-surface px-5 py-4 rounded-xl max-w-[85%] border border-outline-variant/30 shadow-sm chat-bubble-assistant">
            <p class="font-body-md leading-relaxed">
                Hi! I am an AI assistant specialized in Groww Mutual Funds. I can provide factual data like NAVs, expense ratios, and fund managers. How can I help you today?
            </p>
        </div>
    </div>
    
    <!-- Loading State (Hidden by default) -->
    <div id="loading-indicator" class="hidden flex-col items-start gap-2">
        <div class="flex items-center gap-2 bg-surface-container-low/50 px-5 py-3 rounded-full border border-outline-variant/20">
            <div class="loading-dot w-2 h-2 bg-primary/40 rounded-full animate-bounce"></div>
            <div class="loading-dot w-2 h-2 bg-primary/60 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
            <div class="loading-dot w-2 h-2 bg-primary rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
        </div>
    </div>
</div>
<!-- Floating Input Area -->"""
    html = chat_container_pattern.sub(new_chat_container, html)
    
    # 2. Add IDs to input and button
    html = html.replace('<input class="flex-1', '<input id="chat-input" class="flex-1')
    html = html.replace('<button class="bg-primary text-on-primary', '<button id="send-btn" class="bg-primary text-on-primary')
    
    # 3. Add IDs to suggested query buttons
    html = html.replace('"What is the NAV of Navi Nifty 50?"', '"What is the NAV of Navi Nifty 50?"').replace(
        '<button class="text-left text-label-md p-3 rounded-lg border border-outline-variant hover:bg-surface-container-high hover:-translate-y-0.5 transition-all text-on-surface-variant">',
        '<button class="quick-search-btn text-left text-label-md p-3 rounded-lg border border-outline-variant hover:bg-surface-container-high hover:-translate-y-0.5 transition-all text-on-surface-variant">'
    )

    # 4. Replace script
    script_pattern = re.compile(r'<script>.*?</script>', re.DOTALL)
    new_script = """<script>
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const chatContainer = document.getElementById('chat-container');
        const loadingIndicator = document.getElementById('loading-indicator');
        const quickSearchBtns = document.querySelectorAll('.quick-search-btn');
        const groupContainer = input.closest('.relative.group');
        
        input.addEventListener('focus', () => { groupContainer.classList.add('scale-[1.01]'); });
        input.addEventListener('blur', () => { groupContainer.classList.remove('scale-[1.01]'); });

        function appendUserMessage(text) {
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const msgHtml = `
            <div class="flex flex-col items-end gap-2 animate-in fade-in slide-in-from-right-4 duration-500">
                <div class="bg-on-surface text-surface-container-lowest px-5 py-3 rounded-xl max-w-[85%] shadow-sm chat-bubble-user font-body-md">
                    ${text}
                </div>
                <span class="text-label-sm text-on-surface-variant/60 mr-1">${time}</span>
            </div>`;
            loadingIndicator.insertAdjacentHTML('beforebegin', msgHtml);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function appendAssistantMessage(answer, citation, footer) {
            let citationHtml = '';
            if (citation) {
                citationHtml = `
                <div class="flex flex-wrap gap-2 pt-2 border-t border-outline-variant/20 mt-2">
                    <a href="${citation}" target="_blank" class="bg-surface-container-high px-3 py-1 rounded-sm text-label-sm text-on-surface flex items-center gap-2 hover:bg-outline-variant/30 transition-colors">
                        <span class="material-symbols-outlined text-[14px]">link</span>
                        Source Link
                    </a>
                </div>`;
            }
            let footerHtml = '';
            if (footer) {
                footerHtml = `
                <div class="flex items-center gap-2 mt-1">
                    <span class="text-label-sm text-on-surface-variant/60 ml-1">${footer}</span>
                </div>`;
            }

            const msgHtml = `
            <div class="flex flex-col items-start gap-2 animate-in fade-in slide-in-from-left-4 duration-500">
                <div class="flex items-center gap-3 mb-1">
                    <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">smart_toy</span>
                    </div>
                    <span class="text-label-md font-bold text-primary">AI Advisor</span>
                </div>
                <div class="bg-surface-container-low text-on-surface px-5 py-4 rounded-xl max-w-[85%] border border-outline-variant/30 shadow-sm chat-bubble-assistant">
                    <p class="font-body-md leading-relaxed whitespace-pre-wrap">${answer}</p>
                    ${citationHtml}
                </div>
                ${footerHtml}
            </div>`;
            
            loadingIndicator.insertAdjacentHTML('beforebegin', msgHtml);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage(text) {
            if (!text.trim()) return;
            
            input.value = '';
            appendUserMessage(text);
            loadingIndicator.classList.remove('hidden');
            loadingIndicator.classList.add('flex');
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: text })
                });
                const data = await response.json();
                
                loadingIndicator.classList.remove('flex');
                loadingIndicator.classList.add('hidden');
                
                appendAssistantMessage(data.answer, data.citation, data.footer);
            } catch (error) {
                loadingIndicator.classList.remove('flex');
                loadingIndicator.classList.add('hidden');
                appendAssistantMessage("Error connecting to server. Please try again.", null, null);
            }
        }

        sendBtn.addEventListener('click', () => sendMessage(input.value));
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage(input.value);
        });

        quickSearchBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.innerText.replace(/"/g, '').trim();
                sendMessage(text);
            });
        });
    </script>"""
    
    html = script_pattern.sub(new_script, html)
    
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    update_html()
