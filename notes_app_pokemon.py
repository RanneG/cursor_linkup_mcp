"""
Thought Dex — Pokemon-themed Thought Dashboard
A gamified personal thought management system

Run: python notes_app_pokemon.py
Open: http://localhost:5052
"""

import os
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
import re
import json

app = Flask(__name__)
NOTES_FILE = Path(__file__).parent / "NOTES.md"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html class="light" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Thought Dex Trainer Interface</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#ec1313",
                        "background-light": "#f8f6f6",
                        "background-dark": "#221010",
                        "screen-bg": "#fdfcf0",
                        "dex-shadow": "#a60d0d",
                        "exp-blue": "#3b82f6",
                        "hp-green": "#22c55e",
                    },
                    fontFamily: {
                        "display": ["Space Grotesk"]
                    },
                    borderRadius: {"DEFAULT": "0.125rem", "lg": "0.25rem", "xl": "0.5rem", "full": "0.75rem"},
                },
            },
        }
    </script>
    <style>
        .pixel-corners {
            box-shadow: 
                0 -4px 0 0 #1b0d0d,
                0 4px 0 0 #1b0d0d,
                -4px 0 0 0 #1b0d0d,
                4px 0 0 0 #1b0d0d;
        }
        .dex-lcd-screen {
            background-color: #fdfcf0;
            background-image: radial-gradient(#e5e4d3 1px, transparent 1px);
            background-size: 4px 4px;
        }
        .hp-bar-bg {
            background: linear-gradient(to bottom, #444, #222);
        }
        .custom-scrollbar::-webkit-scrollbar { width: 8px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #1b0d0d20; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1b0d0d; border-radius: 4px; }
        
        @keyframes shake {
            0%, 100% { transform: rotate(0deg); }
            25% { transform: rotate(-10deg); }
            75% { transform: rotate(10deg); }
        }
        .pokeball-shake:hover { animation: shake 0.3s ease-in-out; }
        
        @keyframes catchPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
            50% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
        }
        .catch-pulse { animation: catchPulse 1s ease-in-out; }
        
        .toast {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            padding: 1rem 2rem;
            background: #1b0d0d;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            border: 4px solid #ec1313;
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
        
        .chat-expanded {
            position: absolute;
            inset: 1rem;
            z-index: 50;
            width: auto !important;
            height: auto !important;
            background: #fdfcf0;
            border: 8px solid #1b0d0d;
            box-shadow: 0 0 0 100vmax rgba(0,0,0,0.8);
            padding: 1rem;
        }
        .chat-expanded .dex-lcd-screen {
            height: 100%;
        }
        
        /* Quick add modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        .modal-overlay.active { display: flex; }
        
        .modal-content {
            background: #fdfcf0;
            border: 8px solid #1b0d0d;
            padding: 2rem;
            max-width: 400px;
            width: 90%;
        }
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark font-display h-screen flex items-center justify-center p-4 overflow-hidden">

    <!-- Main Pokedex Hardware Frame -->
    <div class="relative w-full max-w-[1600px] h-[calc(100vh-2rem)] max-h-[800px] bg-primary rounded-xl p-4 border-b-[12px] border-dex-shadow flex gap-4 shadow-2xl overflow-hidden border-4 border-[#1b0d0d]">
        
        <!-- Top Indicator Lights -->
        <div class="absolute top-3 left-6 flex items-center gap-4 z-10">
            <div class="size-10 rounded-full bg-blue-400 border-4 border-white shadow-[0_0_15px_rgba(96,165,250,0.8)] pokeball-shake cursor-pointer" onclick="showModal()"></div>
            <div class="flex gap-2">
                <div class="size-3 rounded-full bg-red-800" id="light-1"></div>
                <div class="size-3 rounded-full bg-yellow-400" id="light-2"></div>
                <div class="size-3 rounded-full bg-green-500" id="light-3"></div>
            </div>
        </div>

        <!-- LEFT PANEL: AI Chat -->
        <div class="w-72 flex flex-col gap-3 pt-8 shrink-0">
            <!-- Chat Screen -->
            <div class="flex-1 dex-lcd-screen rounded-lg border-8 border-[#221010] flex flex-col overflow-hidden">
                <!-- Chat Header -->
                <div class="bg-[#1b0d0d] text-white px-4 py-2 flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">smart_toy</span>
                    <span class="font-bold uppercase text-sm">Prof. Oak AI</span>
                    <span class="ml-auto size-2 rounded-full bg-green-500 animate-pulse"></span>
                    <button onclick="toggleChatExpand()" class="ml-2 text-primary hover:text-white transition-colors" title="Expand Chat">
                        <span class="material-symbols-outlined text-sm">open_in_full</span>
                    </button>
                </div>
                
                <!-- Chat Messages -->
                <div class="flex-1 p-3 overflow-y-auto custom-scrollbar space-y-3" id="chat-messages">
                    <div class="flex gap-2">
                        <div class="size-8 rounded-full bg-[#1b0d0d] flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-white text-sm">psychology</span>
                        </div>
                        <div class="bg-white border-2 border-[#1b0d0d] p-2 text-sm text-[#1b0d0d] max-w-[85%]">
                            Hello, Trainer! I'm Prof. Oak. Ask me anything about your thoughts, or request help with tasks!
                        </div>
                    </div>
                </div>
                
                <!-- Chat Input -->
                <div class="p-2 border-t-2 border-[#1b0d0d] bg-white">
                    <div class="flex gap-2">
                        <input type="text" id="chat-input" placeholder="Ask Prof. Oak..." 
                               class="flex-1 p-2 border-2 border-[#1b0d0d] text-sm text-[#1b0d0d] focus:outline-none focus:border-primary"
                               onkeypress="if(event.key==='Enter')sendChat()">
                        <button onclick="sendChat()" class="px-3 bg-primary text-white border-2 border-[#1b0d0d] hover:bg-red-700 transition-colors">
                            <span class="material-symbols-outlined text-sm">send</span>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="grid grid-cols-2 gap-2">
                <button onclick="askOak('Summarize my current thoughts')" class="p-2 bg-[#1b0d0d] text-white text-[10px] font-bold uppercase hover:bg-red-800 transition-colors border-b-2 border-dex-shadow">
                    Summarize
                </button>
                <button onclick="askOak('What should I focus on today?')" class="p-2 bg-[#1b0d0d] text-white text-[10px] font-bold uppercase hover:bg-red-800 transition-colors border-b-2 border-dex-shadow">
                    Prioritize
                </button>
                <button onclick="askOak('Give me a motivational message')" class="p-2 bg-[#1b0d0d] text-white text-[10px] font-bold uppercase hover:bg-red-800 transition-colors border-b-2 border-dex-shadow">
                    Motivate
                </button>
                <button onclick="askOak('Help me brainstorm new ideas')" class="p-2 bg-[#1b0d0d] text-white text-[10px] font-bold uppercase hover:bg-red-800 transition-colors border-b-2 border-dex-shadow">
                    Brainstorm
                </button>
            </div>
        </div>

        <!-- CENTER PANEL: Main Screen -->
        <div class="flex-1 flex flex-col gap-2 min-w-0 pt-8">
            <!-- Central LCD Screen -->
            <div class="flex-1 dex-lcd-screen rounded-lg border-8 border-[#221010] p-4 overflow-y-auto custom-scrollbar min-h-0">
                
                <!-- Screen Header -->
                <header class="flex items-center justify-between border-b-2 border-[#1b0d0d] pb-2 mb-4">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#1b0d0d] text-lg">capture</span>
                        <h1 class="text-[#1b0d0d] text-xl font-bold tracking-tighter uppercase">Thought Dex</h1>
                    </div>
                    <div class="flex items-center gap-4">
                        <div class="flex flex-col items-end">
                            <span class="text-[10px] text-[#9a4c4c] uppercase font-bold">Sync</span>
                            <div class="flex gap-1">
                                <div class="w-1 h-2 bg-[#1b0d0d]"></div>
                                <div class="w-1 h-3 bg-[#1b0d0d]"></div>
                                <div class="w-1 h-4 bg-[#1b0d0d]"></div>
                            </div>
                        </div>
                    </div>
                </header>

                <!-- Wild Thoughts Section (Parking Lot) -->
                <section class="mb-3 border-2 border-[#1b0d0d] bg-white/30">
                    <button onclick="toggleSection('wild')" class="w-full flex justify-between items-center p-2 hover:bg-white/50 transition-colors">
                        <h2 class="text-[#1b0d0d] text-sm font-bold uppercase flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm transition-transform" id="wild-arrow">expand_more</span>
                            <span class="material-symbols-outlined text-sm">grass</span>
                            Wild Thoughts
                            <span class="text-[10px] font-normal text-[#9a4c4c] ml-1" id="wild-count">(0)</span>
                        </h2>
                        <span class="bg-[#1b0d0d] text-screen-bg px-2 py-0.5 text-[10px] font-bold">PARKING LOT</span>
                    </button>
                    <div class="space-y-1 p-2 pt-0" id="wild-thoughts-grid">
                        <!-- Populated by JS -->
                    </div>
                </section>

                <!-- Gym Challenges Section (Priorities) -->
                <section class="mb-3 border-2 border-[#1b0d0d] bg-white/30">
                    <button onclick="toggleSection('gym')" class="w-full flex justify-between items-center p-2 hover:bg-white/50 transition-colors">
                        <h2 class="text-[#1b0d0d] text-sm font-bold uppercase flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm transition-transform" id="gym-arrow">expand_more</span>
                            <span class="material-symbols-outlined text-sm">swords</span>
                            Gym Challenges
                            <span class="text-[10px] font-normal text-[#9a4c4c] ml-1" id="gym-count">(0)</span>
                        </h2>
                        <span class="bg-[#1b0d0d] text-screen-bg px-2 py-0.5 text-[10px] font-bold">PRIORITIES</span>
                    </button>
                    <div class="space-y-2 p-2 pt-0" id="gym-challenges-list">
                        <!-- Populated by JS -->
                    </div>
                </section>

                <!-- Professor's Questions Section -->
                <section class="mb-3 border-2 border-[#1b0d0d] bg-white/30">
                    <button onclick="toggleSection('questions')" class="w-full flex justify-between items-center p-2 hover:bg-white/50 transition-colors">
                        <h2 class="text-[#1b0d0d] text-sm font-bold uppercase flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm transition-transform" id="questions-arrow">expand_more</span>
                            <span class="material-symbols-outlined text-sm">help</span>
                            Prof. Oak's Questions
                            <span class="text-[10px] font-normal text-[#9a4c4c] ml-1" id="questions-count">(0)</span>
                        </h2>
                        <span class="bg-[#1b0d0d] text-screen-bg px-2 py-0.5 text-[10px] font-bold">OPEN</span>
                    </button>
                    <div class="space-y-2 p-2 pt-0" id="questions-list">
                        <!-- Populated by JS -->
                    </div>
                </section>
            </div>

            <!-- Dialogue Box (Professor's Box) -->
            <div class="h-16 bg-[#fdfcf0] border-4 border-[#221010] px-3 py-2 relative flex items-center shrink-0">
                <p class="text-[#1b0d0d] font-medium leading-tight text-sm" id="professor-message">
                    PROF. OAK: "Welcome, Trainer! Click the blue orb to capture a new WILD THOUGHT!"
                </p>
                <div class="absolute bottom-1 right-3 animate-bounce">
                    <span class="material-symbols-outlined text-[#1b0d0d] font-bold rotate-90 text-sm">play_arrow</span>
                </div>
            </div>
        </div>

        <!-- RIGHT PANEL: Stats & Controls -->
        <div class="w-64 flex flex-col gap-3 pt-8 shrink-0">
            
            <!-- Trainer Card -->
            <div class="bg-[#1b0d0d] text-white p-4 rounded-lg border-b-4 border-dex-shadow">
                <div class="flex items-center gap-3 mb-4">
                    <div class="size-12 bg-white rounded-lg border-2 border-primary overflow-hidden flex items-center justify-center">
                        <span class="material-symbols-outlined text-2xl text-primary">person</span>
                    </div>
                    <div>
                        <h2 class="font-bold text-base uppercase tracking-tighter">Trainer</h2>
                        <p class="text-primary text-[10px] font-bold uppercase">LVL <span id="trainer-level">1</span> Thought Trainer</p>
                    </div>
                </div>

                <div class="space-y-2">
                    <div class="flex justify-between text-[10px] font-bold uppercase">
                        <span class="text-gray-400">Thoughts Seen</span>
                        <span id="thoughts-seen">0</span>
                    </div>
                    <div class="flex justify-between text-[10px] font-bold uppercase">
                        <span class="text-gray-400">Thoughts Caught</span>
                        <span id="thoughts-caught">0</span>
                    </div>
                    <div class="flex justify-between text-[10px] font-bold uppercase">
                        <span class="text-gray-400">Badges Earned</span>
                        <div class="flex gap-0.5" id="badges-container">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                </div>

                <div class="mt-4 pt-3 border-t border-white/10">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-[10px] font-bold text-gray-400 uppercase">EXP TO NEXT LVL</span>
                        <span class="text-[10px] font-bold" id="exp-text">0 / 100</span>
                    </div>
                    <div class="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div class="h-full bg-exp-blue transition-all duration-500" id="exp-bar" style="width: 0%"></div>
                    </div>
                </div>
            </div>

            <!-- Menu Navigation -->
            <nav class="space-y-2">
                <button onclick="showModal()" class="w-full flex items-center gap-2 px-3 py-2 bg-[#1b0d0d] text-white rounded border-b-2 border-dex-shadow hover:bg-red-800 transition-colors group">
                    <span class="material-symbols-outlined text-primary group-hover:text-white text-base">add_circle</span>
                    <span class="font-bold uppercase text-xs tracking-wider">New Thought</span>
                </button>
                <button onclick="toggleEditor()" class="w-full flex items-center gap-2 px-3 py-2 bg-[#1b0d0d] text-white rounded border-b-2 border-dex-shadow hover:bg-red-800 transition-colors group">
                    <span class="material-symbols-outlined text-primary group-hover:text-white text-base">edit_note</span>
                    <span class="font-bold uppercase text-xs tracking-wider">Edit Raw</span>
                </button>
                <button onclick="loadNotes()" class="w-full flex items-center gap-2 px-3 py-2 bg-[#1b0d0d] text-white rounded border-b-2 border-dex-shadow hover:bg-red-800 transition-colors group">
                    <span class="material-symbols-outlined text-primary group-hover:text-white text-base">refresh</span>
                    <span class="font-bold uppercase text-xs tracking-wider">Refresh</span>
                </button>
            </nav>

            <!-- A/B Buttons -->
            <div class="flex justify-center gap-4 mt-auto">
                <div class="flex flex-col items-center gap-1">
                    <button onclick="hideModal()" class="size-10 rounded-full bg-[#1b0d0d] border-b-2 border-gray-900 flex items-center justify-center active:translate-y-0.5 active:border-b-0 transition-all">
                        <span class="text-white font-bold text-sm">B</span>
                    </button>
                </div>
                <div class="flex flex-col items-center gap-1">
                    <button onclick="submitNewThought()" class="size-10 rounded-full bg-[#1b0d0d] border-b-2 border-gray-900 flex items-center justify-center active:translate-y-0.5 active:border-b-0 transition-all">
                        <span class="text-white font-bold text-sm">A</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Add Thought Modal -->
    <div class="modal-overlay" id="modal">
        <div class="modal-content">
            <h3 class="text-[#1b0d0d] text-xl font-bold uppercase mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined">catching_pokemon</span>
                Catch New Thought
            </h3>
            <input type="text" id="new-thought-input" placeholder="What wild thought appeared?" 
                   class="w-full p-3 border-4 border-[#1b0d0d] bg-white text-[#1b0d0d] font-bold uppercase text-sm focus:outline-none focus:border-primary mb-4"
                   onkeypress="if(event.key==='Enter')submitNewThought()">
            <div class="flex gap-2">
                <button onclick="hideModal()" class="flex-1 py-2 bg-gray-300 text-[#1b0d0d] font-bold uppercase text-sm border-b-4 border-gray-400">Cancel</button>
                <button onclick="submitNewThought()" class="flex-1 py-2 bg-primary text-white font-bold uppercase text-sm border-b-4 border-dex-shadow">Catch!</button>
            </div>
        </div>
    </div>

    <!-- Editor Modal -->
    <div class="modal-overlay" id="editor-modal">
        <div class="modal-content" style="max-width: 600px;">
            <h3 class="text-[#1b0d0d] text-xl font-bold uppercase mb-4 flex items-center gap-2">
                <span class="material-symbols-outlined">terminal</span>
                Raw Memory Data
            </h3>
            <textarea id="raw-editor" class="w-full h-64 p-3 border-4 border-[#1b0d0d] bg-white text-[#1b0d0d] font-mono text-xs focus:outline-none focus:border-primary mb-4 resize-none"></textarea>
            <div class="flex gap-2">
                <button onclick="hideEditor()" class="flex-1 py-2 bg-gray-300 text-[#1b0d0d] font-bold uppercase text-sm border-b-4 border-gray-400">Cancel</button>
                <button onclick="saveRawEditor()" class="flex-1 py-2 bg-primary text-white font-bold uppercase text-sm border-b-4 border-dex-shadow">Save</button>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div id="toast" class="toast">Saved!</div>

    <script>
        let notesContent = '';
        const thoughtIcons = ['lightbulb', 'bolt', 'star', 'favorite', 'rocket', 'psychology', 'emoji_objects', 'tips_and_updates'];
        const iconColors = ['text-yellow-500', 'text-blue-500', 'text-purple-500', 'text-pink-500', 'text-green-500', 'text-orange-500'];
        
        function getRandomIcon() {
            return thoughtIcons[Math.floor(Math.random() * thoughtIcons.length)];
        }
        
        function getRandomColor() {
            return iconColors[Math.floor(Math.random() * iconColors.length)];
        }

        async function loadNotes() {
            const res = await fetch('/api/notes');
            const data = await res.json();
            notesContent = data.content;
            document.getElementById('raw-editor').value = notesContent;
            parseAndRender();
            updateProfessorMessage("Data synchronized! Your THOUGHT DEX is up to date.");
        }

        async function saveNotes() {
            await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: notesContent })
            });
            showToast('Thought Caught!');
            parseAndRender();
        }

        function parseAndRender() {
            let totalThoughts = 0, caughtThoughts = 0;
            
            // Parse parking lot (Wild Thoughts)
            const parkingMatch = notesContent.match(/## .*Parking Lot[\\s\\S]*?(?=\\n## |$)/);
            let wildHtml = '';
            
            if (parkingMatch) {
                const items = parkingMatch[0].match(/- \\[([ x])\\] (.+)/g) || [];
                items.forEach((item, i) => {
                    const caught = item.includes('[x]');
                    const text = item.replace(/- \\[([ x])\\] /, '');
                    totalThoughts++;
                    if (caught) caughtThoughts++;
                    
                    const num = String(i + 1).padStart(3, '0');
                    
                    if (caught) {
                        wildHtml += `
                            <div class="border-2 border-[#1b0d0d] bg-white/60 p-3 flex items-center gap-3 cursor-pointer hover:bg-white transition-colors group" onclick="toggleThought('${text.replace(/'/g, "\\\\'")}', true)">
                                <div class="size-8 rounded-full bg-green-500 border-2 border-[#1b0d0d] flex items-center justify-center shrink-0">
                                    <span class="material-symbols-outlined text-white text-sm">check</span>
                                </div>
                                <span class="text-[#9a4c4c] text-xs font-bold w-10">#${num}</span>
                                <p class="flex-1 text-[#1b0d0d] font-medium text-sm line-through opacity-50">${text}</p>
                                <span class="bg-green-100 text-green-700 text-[10px] px-2 py-0.5 font-bold uppercase">Caught</span>
                            </div>
                        `;
                    } else {
                        wildHtml += `
                            <div class="border-2 border-[#1b0d0d] bg-[#1b0d0d]/5 p-3 flex items-center gap-3 cursor-pointer hover:bg-white transition-colors group" onclick="toggleThought('${text.replace(/'/g, "\\\\'")}', false)">
                                <div class="size-8 rounded-full bg-white border-2 border-[#1b0d0d] flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:border-primary transition-colors">
                                    <span class="material-symbols-outlined text-[#1b0d0d]/30 text-sm group-hover:text-white transition-colors">radio_button_unchecked</span>
                                </div>
                                <span class="text-[#9a4c4c] text-xs font-bold w-10">#${num}</span>
                                <p class="flex-1 text-[#1b0d0d] font-medium text-sm">${text}</p>
                                <span class="bg-[#1b0d0d] text-white text-[10px] px-2 py-0.5 font-bold uppercase">Wild</span>
                            </div>
                        `;
                    }
                });
            }
            
            document.getElementById('wild-thoughts-grid').innerHTML = wildHtml || '<p class="text-[#9a4c4c] text-center py-4 text-sm">No wild thoughts... Add one!</p>';
            document.getElementById('wild-count').textContent = `(${totalThoughts})`;
            
            // Parse priorities (Gym Challenges)
            const prioritiesMatch = notesContent.match(/## .*Priorities[\\s\\S]*?(?=\\n## |$)/);
            let gymHtml = '';
            let gymCount = 0;
            
            if (prioritiesMatch) {
                const items = prioritiesMatch[0].match(/\\d+\\. \\*\\*(.+?):\\*\\* (.+)/g) || [];
                const gymIcons = ['rocket_launch', 'architecture', 'code', 'brush', 'analytics'];
                const gymColors = ['bg-primary/10 text-primary', 'bg-blue-500/10 text-blue-500', 'bg-green-500/10 text-green-500', 'bg-purple-500/10 text-purple-500', 'bg-orange-500/10 text-orange-500'];
                
                items.forEach((item, i) => {
                    const match = item.match(/\\d+\\. \\*\\*(.+?):\\*\\* (.+)/);
                    if (match) {
                        gymCount++;
                        const hp = 100 - (i * 20);
                        const hpColor = hp > 50 ? 'bg-hp-green' : hp > 20 ? 'bg-yellow-500' : 'bg-red-500';
                        
                        gymHtml += `
                            <div class="border-2 border-[#1b0d0d] bg-white p-3 flex gap-3 items-center">
                                <div class="size-10 rounded-full border-2 border-[#1b0d0d] ${gymColors[i % gymColors.length]} flex items-center justify-center shrink-0">
                                    <span class="material-symbols-outlined text-xl">${gymIcons[i % gymIcons.length]}</span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex justify-between items-end mb-1">
                                        <h3 class="text-[#1b0d0d] font-bold uppercase leading-none text-sm truncate">
                                            <span class="text-primary mr-1 text-xs">#G${gymCount}</span> ${match[1]}
                                        </h3>
                                        <span class="text-[10px] font-bold text-[#1b0d0d] shrink-0 ml-2">HP ${hp}/100</span>
                                    </div>
                                    <div class="w-full h-2 hp-bar-bg border border-[#1b0d0d] p-[1px]">
                                        <div class="h-full ${hpColor}" style="width: ${hp}%"></div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                });
            }
            
            document.getElementById('gym-challenges-list').innerHTML = gymHtml || '<p class="text-[#9a4c4c] text-center py-4 text-sm">No gym challenges set.</p>';
            document.getElementById('gym-count').textContent = `(${gymCount})`;
            
            // Parse questions
            const questionsMatch = notesContent.match(/## .*Open Questions[\\s\\S]*?(?=\\n## |$)/);
            let questionsHtml = '';
            let questionsCount = 0;
            
            if (questionsMatch) {
                const items = questionsMatch[0].match(/- ([^\\[].+)/g) || [];
                items.forEach(item => {
                    const text = item.replace(/^- /, '');
                    if (text.trim()) {
                        questionsCount++;
                        questionsHtml += `
                            <div class="border-2 border-[#1b0d0d] bg-yellow-50 p-2 flex gap-2 items-center">
                                <span class="material-symbols-outlined text-yellow-600 text-base shrink-0">help</span>
                                <span class="text-yellow-700 font-bold text-xs shrink-0">#Q${questionsCount}</span>
                                <p class="text-[#1b0d0d] text-sm">${text}</p>
                            </div>
                        `;
                    }
                });
            }
            
            document.getElementById('questions-list').innerHTML = questionsHtml || '<p class="text-[#9a4c4c] text-center py-4 text-sm">No open questions.</p>';
            document.getElementById('questions-count').textContent = `(${questionsCount})`;
            
            // Update stats
            document.getElementById('thoughts-seen').textContent = totalThoughts;
            document.getElementById('thoughts-caught').textContent = caughtThoughts;
            
            // Calculate level and XP
            const xp = caughtThoughts * 25;
            const level = Math.floor(xp / 100) + 1;
            const xpInLevel = xp % 100;
            
            document.getElementById('trainer-level').textContent = level;
            document.getElementById('exp-text').textContent = `${xpInLevel} / 100`;
            document.getElementById('exp-bar').style.width = `${xpInLevel}%`;
            
            // Update badges
            const badges = Math.floor(caughtThoughts / 3);
            let badgesHtml = '';
            for (let i = 0; i < 8; i++) {
                if (i < badges) {
                    badgesHtml += '<span class="material-symbols-outlined text-sm text-yellow-400">stars</span>';
                } else {
                    badgesHtml += '<span class="material-symbols-outlined text-sm text-gray-600">stars</span>';
                }
            }
            document.getElementById('badges-container').innerHTML = badgesHtml;
        }

        async function toggleThought(text, currentlyCaught) {
            const newCheckbox = currentlyCaught ? '[ ]' : '[x]';
            const oldCheckbox = currentlyCaught ? '[x]' : '[ ]';
            notesContent = notesContent.replace(`- ${oldCheckbox} ${text}`, `- ${newCheckbox} ${text}`);
            
            if (!currentlyCaught) {
                updateProfessorMessage(`Gotcha! "${text}" was caught!`);
                showToast('Thought Caught!');
            } else {
                updateProfessorMessage(`"${text}" was released back into the wild!`);
                showToast('Released!');
            }
            
            await saveNotes();
        }

        async function submitNewThought() {
            const input = document.getElementById('new-thought-input');
            const thought = input.value.trim();
            if (!thought) return;
            
            notesContent = notesContent.replace(/## .*Parking Lot/, `## \\uD83C\\uDD7F\\uFE0F Parking Lot\\n\\n- [ ] ${thought}`);
            input.value = '';
            hideModal();
            
            updateProfessorMessage(`A wild "${thought}" appeared! Quick, catch it before it escapes!`);
            await saveNotes();
        }

        function showModal() {
            document.getElementById('modal').classList.add('active');
            document.getElementById('new-thought-input').focus();
        }

        function hideModal() {
            document.getElementById('modal').classList.remove('active');
        }

        function toggleEditor() {
            document.getElementById('raw-editor').value = notesContent;
            document.getElementById('editor-modal').classList.add('active');
        }

        function hideEditor() {
            document.getElementById('editor-modal').classList.remove('active');
        }

        async function saveRawEditor() {
            notesContent = document.getElementById('raw-editor').value;
            hideEditor();
            await saveNotes();
            updateProfessorMessage("Raw data saved successfully! Your THOUGHT DEX has been updated.");
        }

        function updateProfessorMessage(msg) {
            document.getElementById('professor-message').textContent = `PROF. OAK: "${msg}"`;
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }

        // Section toggle
        const sectionState = {
            wild: true,
            gym: true,
            questions: true
        };

        function toggleSection(section) {
            sectionState[section] = !sectionState[section];
            const content = document.getElementById(
                section === 'wild' ? 'wild-thoughts-grid' : 
                section === 'gym' ? 'gym-challenges-list' : 'questions-list'
            );
            const arrow = document.getElementById(section + '-arrow');
            
            if (sectionState[section]) {
                content.style.display = 'block';
                arrow.style.transform = 'rotate(0deg)';
            } else {
                content.style.display = 'none';
                arrow.style.transform = 'rotate(-90deg)';
            }
            
            // Save state to localStorage
            localStorage.setItem('thoughtdex-sections', JSON.stringify(sectionState));
        }

        function loadSectionState() {
            const saved = localStorage.getItem('thoughtdex-sections');
            if (saved) {
                const state = JSON.parse(saved);
                Object.keys(state).forEach(section => {
                    if (!state[section]) {
                        sectionState[section] = false;
                        toggleSection(section);
                        toggleSection(section); // Toggle twice to set correct state
                    }
                });
            }
        }

        // Chat functions
        function addChatMessage(content, isUser = false) {
            const messagesDiv = document.getElementById('chat-messages');
            const msgHtml = isUser ? `
                <div class="flex gap-2 justify-end">
                    <div class="bg-primary text-white border-2 border-[#1b0d0d] p-2 text-sm max-w-[85%]">
                        ${content}
                    </div>
                    <div class="size-8 rounded-full bg-blue-500 flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-white text-sm">person</span>
                    </div>
                </div>
            ` : `
                <div class="flex gap-2">
                    <div class="size-8 rounded-full bg-[#1b0d0d] flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-white text-sm">psychology</span>
                    </div>
                    <div class="bg-white border-2 border-[#1b0d0d] p-2 text-sm text-[#1b0d0d] max-w-[85%]">
                        ${content}
                    </div>
                </div>
            `;
            messagesDiv.innerHTML += msgHtml;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addTypingIndicator() {
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += `
                <div class="flex gap-2" id="typing-indicator">
                    <div class="size-8 rounded-full bg-[#1b0d0d] flex items-center justify-center shrink-0">
                        <span class="material-symbols-outlined text-white text-sm">psychology</span>
                    </div>
                    <div class="bg-white border-2 border-[#1b0d0d] p-2 text-sm text-[#1b0d0d]">
                        <span class="animate-pulse">Thinking...</span>
                    </div>
                </div>
            `;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function removeTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
        }

        async function sendChat() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;
            
            addChatMessage(message, true);
            input.value = '';
            addTypingIndicator();
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: message,
                        notes_context: notesContent 
                    })
                });
                const data = await res.json();
                removeTypingIndicator();
                addChatMessage(data.response);
                
                if (data.tool_result) {
                    addChatMessage(`[SYSTEM] ${data.tool_result}`);
                }
                
                if (data.refresh_needed) {
                    await loadNotes();
                    updateProfessorMessage("I've updated your Thought Dex based on our conversation!");
                }
            } catch (err) {
                removeTypingIndicator();
                addChatMessage("Sorry, I couldn't connect to the AI. Make sure Ollama is running!");
            }
        }

        function askOak(question) {
            document.getElementById('chat-input').value = question;
            sendChat();
        }

        function toggleChatExpand() {
            const chatPanel = document.querySelector('.w-72'); // Select the left panel
            chatPanel.classList.toggle('chat-expanded');
            
            // Toggle icon
            const btn = chatPanel.querySelector('button[title="Expand Chat"] span');
            if (chatPanel.classList.contains('chat-expanded')) {
                btn.textContent = 'close_fullscreen';
            } else {
                btn.textContent = 'open_in_full';
            }
        }

        // Initialize
        loadNotes();
    </script>
</body>
</html>
'''

# --- Backend Helper Functions ---

def read_notes_content():
    if not NOTES_FILE.exists():
        return ""
    return NOTES_FILE.read_text(encoding='utf-8')

def save_notes_content(content):
    NOTES_FILE.write_text(content, encoding='utf-8')

def add_wild_thought(text):
    content = read_notes_content()
    # Find the Parking Lot section
    marker = "## 🅿️ Parking Lot"
    if marker not in content:
        # If not found, try to find generic or add it
        if "## Parking Lot" in content:
            content = content.replace("## Parking Lot", marker)
        else:
            content += f"\n\n{marker}\n"
    
    # Add item
    # specific naive implementation: replace the header with header + item
    # better: find header, find next header, insert before next header
    
    pattern = r"(## .*Parking Lot.*)(\n)"
    replacement = f"\\1\\2- [ ] {text}\n"
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content, count=1)
    else:
        content += f"\n- [ ] {text}"
        
    save_notes_content(content)
    return f"Added '{text}' to Wild Thoughts."

def add_gym_challenge(title, meta=""):
    content = read_notes_content()
    marker = "## ⚔️ Gym Priorities" # Updating name to match expectations slightly better, or keep standard
    # The JS looks for "Priorities", so let's stick to what works or update it.
    # STARTUP: The file might use "## Gym Priorities" or similar.
    
    # We will search for "Priorities"
    pattern = r"(## .*Priorities.*)(\n)"
    
    # Count existing items to number logic if needed, but simple append is fine for now
    # We need to find the specific list format: "1. **Title:** Desc"
    # Actually, we can just append to the list.
    
    # Let's read the number of items to increment
    current_items = re.findall(r"\d+\. \*\*", content)
    next_num = len(current_items) + 1
    
    new_line = f"{next_num}. **{title}:** {meta}\n"
    
    if re.search(pattern, content):
        # Insert after the header
        content = re.sub(pattern, f"\\1\\2{new_line}", content, count=1)
    else:
        # Append if section not found (fallback)
        content += f"\n\n## ⚔️ Gym Priorities\n{new_line}"
        
    save_notes_content(content)
    return f"Added challenge: {title}"

def add_question(text):
    content = read_notes_content()
    pattern = r"(## .*Open Questions.*)(\n)"
    new_line = f"- {text}\n"
    
    if re.search(pattern, content):
        content = re.sub(pattern, f"\\1\\2{new_line}", content, count=1)
    else:
        content += f"\n\n## ❓ Open Questions\n{new_line}"
        
    save_notes_content(content)
    return f"Logged question: {text}"

def get_thought_by_index(index):
    """Helper to find the text of the N-th wild thought (1-based index)"""
    content = read_notes_content()
    # Find Parker Lot section
    pattern = r"## .*Parking Lot([\s\S]*?)(?=## |$)"
    match = re.search(pattern, content)
    if not match:
        return None
        
    # Extract list items
    section_content = match.group(1)
    # Match lines starting with "- [ ]" or "- [x]"
    items = re.findall(r"-\s\[[ x]\]\s(.+)", section_content)
    
    if 0 < index <= len(items):
        return items[index-1].strip()
    return None

def edit_thought(old_text, new_text):
    content = read_notes_content()
    target_text = old_text
    
    # Check if old_text is an ID like #001 or just 1
    id_match = re.match(r"#?(\d+)$", old_text.strip())
    if id_match:
        index = int(id_match.group(1))
        found_text = get_thought_by_index(index)
        if found_text:
            target_text = found_text
        else:
            return f"Error: Could not find thought #{index}"

    # Simple replace
    # We need to be careful to only replace the text in the list line, not globally if possible
    # But for now, simple replace is safer than complex regex if the text is unique enough.
    # To be safer, we can match the exact list item line.
    
    # Escape special regex chars in target_text
    safe_target = re.escape(target_text)
    pattern = f"(-\s\[[ x]\]\s){safe_target}(?=\s|$)"
    
    if re.search(pattern, content):
        content = re.sub(pattern, f"\\1{new_text}", content, count=1)
        save_notes_content(content)
        return f"Updated '{target_text}' to '{new_text}'."
        
    return f"Could not find '{old_text}' to update."

def remove_thought(text):
    content = read_notes_content()
    target_text = text
    
    # Check if text is an ID
    id_match = re.match(r"#?(\d+)$", text.strip())
    if id_match:
        index = int(id_match.group(1))
        found_text = get_thought_by_index(index)
        if found_text:
            target_text = found_text
        else:
            return f"Error: Could not find thought #{index}"
            
    # Regex to remove the whole line containing the text
    safe_text = re.escape(target_text)
    pattern = f"^.*-\s\[[ x]\]\s{safe_text}.*$\\n?"
    
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, "", content, flags=re.MULTILINE)
        save_notes_content(content)
        return f"Removed '{target_text}'."
    return f"Could not find '{text}' to remove."



@app.route('/')
def index():
    content = ""
    if NOTES_FILE.exists():
        content = NOTES_FILE.read_text(encoding='utf-8')
    return render_template_string(HTML_TEMPLATE, content=content)

@app.route('/api/notes', methods=['GET'])
def get_notes():
    content = ""
    if NOTES_FILE.exists():
        content = NOTES_FILE.read_text(encoding='utf-8')
    return jsonify({'content': content})

@app.route('/api/notes', methods=['POST'])
def save_notes():
    data = request.json
    content = data.get('content', '')
    NOTES_FILE.write_text(content, encoding='utf-8')
    return jsonify({'status': 'ok'})


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint using Ollama"""
    import requests
    
    data = request.json
    message = data.get('message', '')
    notes_context = data.get('notes_context', '')
    
    # --- Context Intelligence Logic ---
    # Parse the notes to map IDs (matching Frontend visual order) to content
    formatted_lines = []
    
    current_section = None
    wild_count = 0
    gym_count = 0
    question_count = 0
    
    for line in notes_context.split('\n'):
        # Detect Sections
        if "##" in line and "Parking Lot" in line:
            current_section = "wild"
            formatted_lines.append(line)
            continue
        elif "##" in line and "Priorities" in line:
            current_section = "gym"
            formatted_lines.append(line)
            continue
        elif "##" in line and "Open Questions" in line:
            current_section = "questions"
            formatted_lines.append(line)
            continue
        elif line.startswith("## "):
            current_section = "other"
            formatted_lines.append(line)
            continue
            
        # Process Items based on Section
        if current_section == "wild" and re.match(r"^\s*-\s\[[ x]\]", line):
            wild_count += 1
            formatted_lines.append(f"(ID: #{wild_count:03d}) {line}")
        elif current_section == "gym" and re.match(r"^\d+\.", line):
            gym_count += 1
            formatted_lines.append(f"(Gym ID: #{gym_count}) {line}")
        elif current_section == "questions" and line.strip().startswith("- "):
            question_count += 1
            formatted_lines.append(f"(Question ID: #{question_count}) {line}")
        else:
            formatted_lines.append(line)
            
    formatted_context = '\n'.join(formatted_lines)

    # --- System Prompt Refinement ---
    tools_desc = """
You have access to the following tools to modify the Thought Dex. 
If the user asks to do something that requires these tools, OUTPUT A JSON OBJECT at the END of your response.
Format:
RESPONSE TEXT
^^^JSON^^^
{"tool": "tool_name", "args": {"arg1": "value"}}

Tools strategies:
- If user has a new idea/thought -> tool: "add_thought", args: {"text": "..."}
- If user wants to change a thought -> tool: "edit_thought", args: {"old_text": "...", "new_text": "..."}
- If user wants to delete/remove something -> tool: "remove_thought", args: {"text": "..."}
  - IMPORTANT: You can refer to thoughts by their ID (e.g. #001) or their text.
- If user has a specific task/goal -> tool: "add_challenge", args: {"title": "...", "meta": "details or deadline"}
- If user asks a question you can't allow or wants to save a question -> tool: "log_question", args: {"text": "..."}
- ALWAYS being a "Time Management Coach". If a task has no deadline, ask for one or suggest one in the metadata.
"""

    system_prompt = f"""You are Prof. Oak, a rational and highly intelligent research assistant in the "Thought Dex".
Your goal is to help the user manage their knowledge and tasks efficiently.
You have access to the user's notes and should refer to them by ID (e.g., #001) when appropriate.
Be concise, logical, and helpful. Use Pokemon metaphors only sparingly or when encouraged.
{tools_desc}
"""
    
    prompt = f"""{system_prompt}

Current Notes Context:
---
{formatted_context[:5000]}
---

Trainer's Input: {message}

Prof. Oak's Response:"""
    
    try:
        # Call Ollama API
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 300
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            full_response = result.get('response', '')
            
            # Parse for tool calls
            tool_response = ""
            run_refresh = False
            
            if "^^^JSON^^^" in full_response:
                text_part, json_part = full_response.split("^^^JSON^^^", 1)
                text_part = text_part.strip()
                
                try:
                    tool_data = json.loads(json_part.strip())
                    tool_name = tool_data.get('tool')
                    args = tool_data.get('args', {})
                    
                    if tool_name == 'add_thought':
                        tool_response = add_wild_thought(args.get('text'))
                        run_refresh = True
                    elif tool_name == 'edit_thought':
                        tool_response = edit_thought(args.get('old_text'), args.get('new_text'))
                        run_refresh = True
                    elif tool_name == 'remove_thought':
                        tool_response = remove_thought(args.get('text'))
                        run_refresh = True
                    elif tool_name == 'add_challenge':
                        tool_response = add_gym_challenge(args.get('title'), args.get('meta', ''))
                        run_refresh = True
                    elif tool_name == 'log_question':
                        tool_response = add_question(args.get('text'))
                        run_refresh = True
                        
                except Exception as e:
                    tool_response = f"Error executing tool: {e}"
                
                final_response = text_part
            else:
                final_response = full_response
                
            return jsonify({
                'response': final_response,
                'tool_result': tool_response,
                'refresh_needed': run_refresh
            })
        else:
            return jsonify({'response': f'Ollama error: {response.status_code}'})
            
    except requests.exceptions.ConnectionError:
        return jsonify({'response': 'Cannot connect to Ollama. Make sure it is running!'})
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'})


if __name__ == '__main__':
    print("Thought Dex - Pokemon Thought Dashboard")
    print("=" * 50)
    print(f"Notes file: {NOTES_FILE}")
    print(f"Open: http://localhost:5052")
    print("=" * 50)
    app.run(port=5052, debug=True)

