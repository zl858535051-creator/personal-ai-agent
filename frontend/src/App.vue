<template>
  <div class="shell">
    <aside class="sidebar">
      <h1>AI Agent</h1>
      <nav>
        <RouterLink to="/">Chat</RouterLink>
        <RouterLink to="/upload">Files</RouterLink>
        <RouterLink to="/history">History</RouterLink>
        <RouterLink to="/reports">Reports</RouterLink>
      </nav>
    </aside>
    <main class="workspace">
      <RouterView />
    </main>
  </div>
</template>

