// Tabelas responsivas: DataTables só cuida de esconder colunas (sem rolagem horizontal).
// Busca, ordenação e paginação continuam no servidor (django-filter e paginação do Django).
(function ($) {
  if (!$.fn.DataTable) return;

  $('table.js-tabela').each(function () {
    var tabela = $(this);
    var api = tabela.DataTable({
      // tipo próprio + alvo: nenhum ícone de +/−. Tocar na primeira célula da linha abre e fecha os detalhes.
      responsive: { details: { type: 'toque', target: 'td:first-child' } },
      paging: false,
      searching: false,
      ordering: true,      // ordena só os registros da página atual; use data-order nas células (datas, valores)
      order: [],           // mantém a ordem que veio do servidor até o usuário clicar em um título
      orderMulti: false,
      info: false,
      autoWidth: false,
      layout: { topStart: null, topEnd: null, bottomStart: null, bottomEnd: null }
    });

    // dica só enquanto houver colunas escondidas (celular)
    var dica = $('<p class="fin-dica-toque" hidden><i class="bi bi-hand-index-thumb me-1"></i>Toque em uma linha para ver mais detalhes.</p>');
    tabela.closest('.fin-table-wrap').before(dica);
    var atualizar = function () { dica.prop('hidden', !tabela.hasClass('collapsed')); };
    api.on('responsive-resize', atualizar);
    atualizar();
  });

  // a barra do topo ganha mais sombra quando a página rola
  var barra = document.getElementById('navTopo');
  if (barra) {
    var marcar = function () { barra.classList.toggle('rolou', window.scrollY > 8); };
    window.addEventListener('scroll', marcar, { passive: true });
    marcar();
  }
})(window.jQuery);

// menus da navbar: abrem no clique e fecham quando o mouse sai de cima (desktop com mouse).
// Vale para todos: Lançamentos, Cadastros, Novo e usuário. No celular seguem só o toque.
(function () {
  var mq = window.matchMedia('(min-width: 992px) and (hover: hover)');
  document.querySelectorAll('.fin-navbar .dropdown').forEach(function (item) {
    var toggle = item.querySelector('[data-bs-toggle="dropdown"]');
    var timer;
    item.addEventListener('mouseenter', function () { window.clearTimeout(timer); });
    item.addEventListener('mouseleave', function () {
      if (!mq.matches) return;
      timer = window.setTimeout(function () {
        var menu = bootstrap.Dropdown.getInstance(toggle);
        if (menu) menu.hide();
      }, 200);
    });
  });
})();
