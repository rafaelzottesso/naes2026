// Tabelas responsivas: DataTables só cuida de esconder colunas (sem rolagem horizontal).
// Busca, ordenação e paginação continuam no servidor (django-filter e paginação do Django).
(function ($) {
  if (!$.fn.DataTable) return;

  $('table.js-tabela').each(function () {
    $(this).DataTable({
      responsive: true,
      paging: false,
      searching: false,
      ordering: false,
      info: false,
      autoWidth: false,
      layout: { topStart: null, topEnd: null, bottomStart: null, bottomEnd: null }
    });
  });

  // a barra do topo ganha mais sombra quando a página rola
  var barra = document.getElementById('navTopo');
  if (barra) {
    var marcar = function () { barra.classList.toggle('rolou', window.scrollY > 8); };
    window.addEventListener('scroll', marcar, { passive: true });
    marcar();
  }
})(window.jQuery);

// menus do topo abrem ao passar o mouse (só no desktop com mouse). Usa a API do Bootstrap,
// então o posicionamento é o mesmo do clique; os menus da direita (Novo e usuário) abrem só no clique.
(function () {
  var mq = window.matchMedia('(min-width: 992px) and (hover: hover)');
  document.querySelectorAll('.fin-navbar .navbar-nav .dropdown').forEach(function (item) {
    var toggle = item.querySelector('[data-bs-toggle="dropdown"]');
    var timer;
    item.addEventListener('mouseenter', function () {
      if (!mq.matches) return;
      window.clearTimeout(timer);
      bootstrap.Dropdown.getOrCreateInstance(toggle).show();
    });
    item.addEventListener('mouseleave', function () {
      if (!mq.matches) return;
      timer = window.setTimeout(function () { bootstrap.Dropdown.getOrCreateInstance(toggle).hide(); }, 150);
    });
  });
})();
