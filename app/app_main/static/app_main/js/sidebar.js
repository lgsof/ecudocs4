<script>
  // Works with Bootstrap 4. For Bootstrap 5, change events to 'shown.bs.collapse' / 'hidden.bs.collapse'
  document.addEventListener('DOMContentLoaded', function () {
    const sections = ['cartaporte','manifiesto','declaracion','entidades','usuario','administracion'];
    sections.forEach(id => {
      const key = `sb-open-${id}`;
      const el = document.getElementById(id);
      if (!el) return;
      // restore
      if (localStorage.getItem(key) === '1') el.classList.add('show');
      // listen
      $(el).on('shown.bs.collapse', () => localStorage.setItem(key, '1'));
      $(el).on('hidden.bs.collapse', () => localStorage.setItem(key, '0'));
    });
  });
</script>

