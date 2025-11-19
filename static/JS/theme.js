document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;

  const root = document.documentElement; // <html>

  // Cargar tema guardado
  const saved = localStorage.getItem('theme');

  if (saved === 'dark') {
    root.classList.add('dark');
  } else if (saved === 'light') {
    root.classList.remove('dark');
  } else {
    // Si no hay guardado, usa preferencia del sistema
    if (window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: dark)').matches) {
      root.classList.add('dark');
    }
  }

  // Al hacer click, alternar
  btn.addEventListener('click', () => {
    const isDark = root.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });
});
