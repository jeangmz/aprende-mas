<script>
  import { onMount } from 'svelte';
  import { marked } from 'marked';
  import {
    Brain, BrainCircuit, Sparkles, Trash2, Smile, User,
    Palette, Dog, Calculator, BookOpen,
    Send, PanelLeft, MessageSquare, Clock3
  } from 'lucide-svelte';

  let messages = $state([]);
  let inputMessage = $state('');
  let isLoading = $state(false);
  let sessionId = $state(null);
  let sessionTitle = $state('');
  let messagesContainer = $state(null);
  let sessions = $state([]);
  let sidebarOpen = $state(false);
  let sidebarCollapsed = $state(false);
  let userName = $state('usuario');
  let editingName = $state(false);
  let tempName = $state('');
  let currentGame = $state(null);
  let gameQuestion = $state('');
  let gameOptions = $state([]);
  let gameAnswer = $state('');
  const API_URL = '/api';

  const GAMES = {
    colors: {
      title: 'Colores',
      prompt: 'Enséñame los colores en inglés con ejemplos.',
      icon: Palette
    },
    animals: {
      title: 'Animales',
      prompt: 'Enséñame los nombres de animales en inglés.',
      icon: Dog
    },
    numbers: {
      title: 'Números',
      prompt: 'Enséñame los números en inglés.',
      icon: Calculator
    },
    story: {
      title: 'Cuentos',
      prompt: 'Cuéntame un cuento corto en inglés.',
      icon: BookOpen
    }
  };

  onMount(() => {
    const savedName = localStorage.getItem('leximind_username');
    if (savedName) userName = savedName;
    sidebarCollapsed = localStorage.getItem('leximind_sidebar_collapsed') === 'true';
    loadSessions();
  });

  async function loadSessions() {
    try {
      const res = await fetch(`${API_URL}/sessions`);
      sessions = await res.json();
    } catch {}
  }

  async function loadHistory(id) {
    try {
      const res = await fetch(`${API_URL}/sessions/${id}/history`);
      const data = await res.json();
      sessionId = id;
      messages = data.history.map((h) => [
        { role: 'user', content: h.user },
        { role: 'assistant', content: h.assistant }
      ]).flat();
      sessionTitle = sessions.find((s) => s.session_id === id)?.title || 'Chat';
      scrollToBottom();
    } catch {}
  }

  async function deleteSession(id, e) {
    e.stopPropagation();
    try {
      await fetch(`${API_URL}/sessions/${id}`, { method: 'DELETE' });
      if (sessionId === id) {
        messages = [];
        sessionId = null;
        sessionTitle = '';
      }
      loadSessions();
    } catch {}
  }

  function startNewChat() {
    messages = [];
    sessionId = null;
    sessionTitle = '';
    currentGame = null;
    sidebarOpen = false;
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  function toggleSidebarCollapsed() {
    sidebarCollapsed = !sidebarCollapsed;
    localStorage.setItem('leximind_sidebar_collapsed', String(sidebarCollapsed));
  }

  function handleSidebarButton() {
    if (window.matchMedia('(min-width: 1024px)').matches) {
      toggleSidebarCollapsed();
      return;
    }
    toggleSidebar();
  }

  function startEditName() {
    tempName = userName;
    editingName = true;
  }

  function saveName() {
    if (tempName.trim()) {
      userName = tempName.trim();
      localStorage.setItem('leximind_username', userName);
    }
    editingName = false;
  }

  function handleNameKeydown(e) {
    if (e.key === 'Enter') saveName();
    if (e.key === 'Escape') editingName = false;
  }

  function startGame(gameKey) {
    const game = GAMES[gameKey];
    if (game) {
      currentGame = gameKey;
      inputMessage = game.prompt;
      sendMessage();
    }
  }

  async function sendMessage() {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    inputMessage = '';

    messages = [...messages, { role: 'user', content: userMessage }];
    scrollToBottom();
    isLoading = true;

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, session_id: sessionId })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      let started = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                fullContent += data.token;
                if (!started) {
                  started = true;
                  messages = [...messages, { role: 'assistant', content: fullContent }];
                } else {
                  messages[messages.length - 1] = { ...messages[messages.length - 1], content: fullContent };
                }
              }
              if (data.session_id) sessionId = data.session_id;
              if (data.title) sessionTitle = data.title;
            } catch {}
          }
        }
        scrollToBottom();
      }

      loadSessions();
    } catch {
      messages = [...messages, { role: 'assistant', content: '¡Ups! Algo salió mal. Inténtalo de nuevo.' }];
    } finally {
      isLoading = false;
      scrollToBottom();
    }
  }

  function scrollToBottom() {
    if (messagesContainer) {
      setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }, 10);
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es', { month: 'short', day: 'numeric' });
  }

  function getInitial(str) {
    return str ? str.charAt(0).toUpperCase() : 'A';
  }
</script>

<div class="flex h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.18),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(59,130,246,0.12),_transparent_28%),linear-gradient(180deg,_#fbfdff_0%,_#f2f8ff_42%,_#eef6ff_100%)] text-slate-800">
  <div
    class={`fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm transition-opacity duration-300 lg:hidden ${sidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
    role="button"
    tabindex="0"
    onkeydown={() => {}}
    onclick={toggleSidebar}
  ></div>

  <aside class={`fixed inset-y-0 left-0 z-50 flex w-[290px] flex-col border-r border-white/60 bg-white/78 shadow-[0_30px_80px_rgba(109,40,217,0.18)] backdrop-blur-2xl transition-all duration-300 lg:static lg:z-0 lg:translate-x-0 ${sidebarCollapsed ? 'lg:w-[96px]' : 'lg:w-[290px]'} ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
    <div class={`border-b border-blue-100/80 pb-5 pt-6 ${sidebarCollapsed ? 'px-3' : 'px-5'}`}>
      <div class={`mb-4 flex items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'}`}>
        <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 via-blue-500 to-sky-400 text-white shadow-lg shadow-blue-200">
          <Brain class="h-6 w-6" stroke-width="1.8" />
        </div>
        {#if !sidebarCollapsed}
          <div class="text-lg font-black tracking-tight text-slate-900">Aprende+</div>
        {/if}
      </div>

      <button
        onclick={startNewChat}
        class={`flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-blue-600 via-blue-500 to-sky-500 py-3 font-bold text-white shadow-lg shadow-blue-200 transition-all hover:-translate-y-0.5 hover:shadow-xl cursor-pointer ${sidebarCollapsed ? 'px-0' : 'gap-2 px-4'}`}
        aria-label="Nuevo chat"
      >
        <Sparkles class="h-4 w-4" />
        {#if !sidebarCollapsed}
          Nuevo chat
        {/if}
      </button>
    </div>

    {#if !sidebarCollapsed}
      <div class="px-5 py-4">
        <div class="rounded-3xl border border-blue-100 bg-gradient-to-br from-blue-50 to-white p-4 shadow-sm">
          <div class="mb-3 flex items-center justify-between">
            <div class="text-sm font-semibold text-slate-700">Tu espacio</div>
            <div class="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-blue-700 shadow-sm">
              {sessions.length} chats
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="rounded-2xl bg-white/90 p-3 shadow-sm">
              <div class="mb-1 flex items-center gap-2 text-slate-500">
                <MessageSquare class="h-4 w-4 text-blue-500" />
                Historial
              </div>
              <div class="text-lg font-black text-slate-900">{messages.length}</div>
            </div>
            <div class="rounded-2xl bg-white/90 p-3 shadow-sm">
              <div class="mb-1 flex items-center gap-2 text-slate-500">
                <Clock3 class="h-4 w-4 text-blue-500" />
                Sesión
              </div>
              <div class="truncate text-sm font-bold text-slate-900">{sessionTitle || 'Nueva conversación'}</div>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <div class={`min-h-0 flex-1 pb-4 ${sidebarCollapsed ? 'px-2 pt-4' : 'px-4'}`}>
      {#if !sidebarCollapsed}
        <div class="mb-3 flex items-center justify-between px-1">
          <div class="text-xs font-bold uppercase tracking-[0.22em] text-slate-400">Recientes</div>
          <div class="text-xs text-slate-400">Local</div>
        </div>
      {/if}

      <div class="scrollbar-thin h-full space-y-2 overflow-y-auto pr-1">
        {#each sessions as session}
          <div class="group relative">
            <button
              onclick={() => { loadHistory(session.session_id); sidebarOpen = false; }}
              class={`w-full rounded-2xl border text-left transition-all cursor-pointer ${sidebarCollapsed ? 'p-2.5' : 'p-3.5 pr-10'} ${sessionId === session.session_id ? 'border-blue-200 bg-gradient-to-r from-blue-100/90 to-sky-50 shadow-md shadow-blue-100' : 'border-transparent bg-white/75 hover:border-blue-100 hover:bg-white hover:shadow-sm'}`}
              aria-label={session.title || 'Chat'}
            >
              <div class={`flex min-w-0 items-center ${sidebarCollapsed ? 'justify-center' : 'gap-3'}`}>
                <div class={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl text-sm font-black ${sessionId === session.session_id ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700'}`}>
                  {getInitial(session.title || 'C')}
                </div>
                {#if !sidebarCollapsed}
                  <div class="min-w-0">
                    <div class="truncate text-sm font-bold text-slate-800">{session.title || 'Chat'}</div>
                    <div class="mt-0.5 text-xs text-slate-500">{session.message_count} mensajes</div>
                  </div>
                {/if}
              </div>
              {#if !sidebarCollapsed}
                <div class="mt-2 text-xs text-slate-400">{formatDate(session.last_activity)}</div>
              {/if}
            </button>
            {#if !sidebarCollapsed}
              <button
                onclick={(e) => deleteSession(session.session_id, e)}
                class="absolute right-3 top-3 rounded-xl p-2 text-slate-400 opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 cursor-pointer"
                aria-label="Eliminar chat"
              >
                <Trash2 class="h-4 w-4" />
              </button>
            {/if}
          </div>
        {/each}

        {#if sessions.length === 0}
          <div class={`rounded-3xl border border-dashed border-blue-200 bg-white/70 text-center text-sm text-slate-500 ${sidebarCollapsed ? 'p-3' : 'p-5'}`}>
            {#if sidebarCollapsed}
              <MessageSquare class="mx-auto h-5 w-5 text-blue-400" />
            {:else}
              Tus conversaciones aparecerán aquí cuando empieces a practicar.
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </aside>

  <main class="flex min-w-0 flex-1 flex-col">
    <header class="border-b border-white/70 bg-white/65 px-4 py-4 shadow-[0_12px_30px_rgba(109,40,217,0.06)] backdrop-blur-xl md:px-6">
      <div class="mx-auto flex w-full max-w-6xl items-center justify-between gap-4">
        <div class="flex min-w-0 items-center gap-3">
          <button
            onclick={handleSidebarButton}
            class="rounded-2xl border border-blue-200 bg-white p-2.5 text-blue-700 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
            aria-label="Alternar sidebar"
          >
            <PanelLeft class={`h-5 w-5 transition-transform duration-300 ${sidebarCollapsed ? 'rotate-180' : ''}`} />
          </button>

          <div class="min-w-0">
            {#if currentGame}
              <div class="mb-1 flex items-center gap-2">
                <div class="rounded-full bg-blue-100 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.2em] text-blue-700">
                  {GAMES[currentGame].title}
                </div>
              </div>
            {/if}
            <div class="truncate text-xl font-black tracking-tight text-slate-900">
              {sessionTitle || 'Nueva conversación'}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          {#if editingName}
            <input
              type="text"
              bind:value={tempName}
              onkeydown={handleNameKeydown}
              onblur={saveName}
              class="w-32 rounded-2xl border border-blue-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none ring-0 transition focus:border-blue-400 focus:shadow-[0_0_0_4px_rgba(59,130,246,0.12)]"
            />
          {:else}
            <button
              onclick={startEditName}
              class="flex items-center gap-3 rounded-2xl border border-white/80 bg-white px-3 py-2 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
            >
              <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-sky-100 text-blue-700">
                <Smile class="h-5 w-5" />
              </div>
              <div class="hidden text-left sm:block">
                <div class="text-xs uppercase tracking-[0.18em] text-slate-400">Perfil</div>
                <div class="text-sm font-bold text-slate-800">{userName}</div>
              </div>
            </button>
          {/if}
        </div>
      </div>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto px-4 py-5 md:px-6" bind:this={messagesContainer}>
      <div class="mx-auto flex min-h-full w-full max-w-5xl flex-col">
        {#if messages.length === 0}
          <section class="flex flex-1 items-center justify-center py-6">
            <div class="w-full max-w-4xl rounded-[32px] border border-white/80 bg-white/68 p-6 shadow-[0_30px_80px_rgba(37,99,235,0.10)] backdrop-blur-xl md:p-8">
              <div class="mx-auto max-w-3xl text-center">
                <div class="mx-auto mb-5 flex h-[72px] w-[72px] items-center justify-center rounded-[28px] bg-gradient-to-br from-blue-600 via-blue-500 to-sky-500 text-white shadow-lg shadow-blue-200">
                  <BrainCircuit class="h-10 w-10" stroke-width="1.7" />
                </div>
                <h1 class="text-4xl font-black leading-tight tracking-tight text-slate-900 md:text-5xl">
                  Hola, {userName}
                </h1>
                <p class="mt-4 text-base leading-7 text-slate-600">
                  Elige un tema o escribe tu pregunta para empezar.
                </p>

                <div class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {#each Object.entries(GAMES) as [key, { title, icon: Icon }]}
                    <button
                      onclick={() => startGame(key)}
                      class="group rounded-3xl border border-blue-100 bg-white p-4 text-left shadow-sm transition-all hover:-translate-y-1 hover:border-blue-300 hover:shadow-lg cursor-pointer"
                    >
                      <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-100 to-sky-100 text-blue-700 transition-transform group-hover:scale-105">
                        <Icon class="h-6 w-6" />
                      </div>
                      <div class="text-base font-black text-slate-900">{title}</div>
                    </button>
                  {/each}
                </div>
              </div>
            </div>
          </section>
        {/if}

        {#if messages.length > 0}
          <section class="space-y-5 py-2">
            {#each messages as message}
              {#if message.role !== 'system'}
                <div class={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div class={`flex w-full max-w-3xl gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div class={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl shadow-lg ${message.role === 'user' ? 'bg-gradient-to-br from-slate-800 to-slate-700 text-white shadow-slate-200' : 'bg-gradient-to-br from-blue-600 via-blue-500 to-sky-500 text-white shadow-blue-200'}`}>
                      {#if message.role === 'user'}
                        <User class="h-5 w-5" />
                      {:else}
                        <BrainCircuit class="h-5 w-5" />
                      {/if}
                    </div>

                    <div class={`min-w-0 flex-1 rounded-[26px] border px-5 py-4 shadow-sm ${message.role === 'user' ? 'border-slate-200 bg-white text-slate-800' : 'border-blue-100 bg-white/92 text-slate-800 shadow-[0_18px_45px_rgba(37,99,235,0.08)]'}`}>
                      <div class="mb-2 flex items-center justify-between gap-3">
                        <div class={`text-xs font-bold uppercase tracking-[0.22em] ${message.role === 'user' ? 'text-slate-400' : 'text-blue-500'}`}>
                          {message.role === 'user' ? userName : 'Aprende+'}
                        </div>
                      </div>
                      <div class="prose prose-sm max-w-none text-[15px] leading-7 prose-headings:text-slate-900 prose-p:text-slate-700 prose-strong:text-slate-900 prose-li:text-slate-700">
                        {@html marked.parse(message.content)}
                      </div>
                    </div>
                  </div>
                </div>
              {/if}
            {/each}

            {#if isLoading && messages[messages.length - 1].role === 'user'}
              <div class="flex justify-start">
                <div class="flex w-full max-w-3xl gap-4">
                  <div class="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 via-blue-500 to-sky-500 text-white shadow-lg shadow-blue-200">
                    <BrainCircuit class="h-5 w-5" />
                  </div>
                  <div class="rounded-[26px] border border-blue-100 bg-white/92 px-5 py-4 shadow-[0_18px_45px_rgba(37,99,235,0.08)]">
                    <div class="mb-2 text-xs font-bold uppercase tracking-[0.22em] text-blue-500">Aprende+</div>
                    <div class="flex gap-1.5">
                      <span class="h-2 w-2 rounded-full bg-blue-400 animate-bounce"></span>
                      <span class="h-2 w-2 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 0.15s"></span>
                      <span class="h-2 w-2 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 0.3s"></span>
                    </div>
                  </div>
                </div>
              </div>
            {/if}
          </section>
        {/if}
      </div>
    </div>

    <div class="border-t border-white/70 bg-white/70 px-4 py-4 backdrop-blur-xl md:px-6">
      <div class="mx-auto w-full max-w-5xl">
        <div class="rounded-[30px] border border-white/80 bg-white/90 p-3 shadow-[0_24px_60px_rgba(109,40,217,0.10)]">
          <div class="mb-2 flex flex-wrap items-center justify-between gap-2 px-2">
            <div class="text-sm font-semibold text-slate-600">
              {isLoading ? 'Aprende+ está escribiendo...' : 'Escribe tu siguiente mensaje'}
            </div>
            <div class="text-xs text-slate-400">
              `Enter` envía, `Shift + Enter` agrega una línea
            </div>
          </div>

          <div class="flex items-end gap-3">
            <textarea
              bind:value={inputMessage}
              placeholder="Pregunta cualquier cosa para aprender inglés"
              onkeydown={handleKeydown}
              disabled={isLoading}
              rows="1"
              class="min-h-[56px] flex-1 resize-none rounded-[24px] border border-blue-100 bg-[linear-gradient(180deg,_#ffffff_0%,_#f4f9ff_100%)] px-5 py-4 text-[15px] text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-blue-300 focus:shadow-[0_0_0_4px_rgba(59,130,246,0.12)] disabled:cursor-not-allowed disabled:opacity-70"
            ></textarea>

            <button
              onclick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
              class="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-[22px] bg-gradient-to-r from-blue-600 via-blue-500 to-sky-500 text-white shadow-lg shadow-blue-200 transition-all hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
              aria-label="Enviar"
            >
              <Send class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  .scrollbar-thin::-webkit-scrollbar {
    width: 8px;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #93c5fd 0%, #60a5fa 100%);
    border-radius: 999px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #60a5fa 0%, #2563eb 100%);
  }
</style>



