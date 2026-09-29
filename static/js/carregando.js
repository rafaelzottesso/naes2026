/*
 * Botões com estado de "carregando" (padrão do AnotAI).
 *
 * O que faz:
 *  - Todo <form> ganha o comportamento sozinho, sem classe nem script extra.
 *  - No envio, o botão que enviou troca o rótulo por um spinner + texto e fica
 *    inerte. O formulário não deixa enviar de novo enquanto espera.
 *  - O botão volta ao estado original em TODOS estes casos:
 *      1. o usuário navega e volta (botão "voltar", bfcache): eventos pagehide e pageshow;
 *      2. a resposta não troca de página (download, erro de rede): tempo limite;
 *      3. outro script cancelou o envio (validação): nem chega a entrar em carregando;
 *      4. a página é recarregada: o HTML já vem no estado original.
 *
 * Como personalizar (atributos no botão):
 *  - data-texto-carregando="Excluindo..."   texto ao lado do spinner (padrão: "Enviando...")
 *  - formulário com data-sem-carregando     não aplica o comportamento
 *
 * Para envios feitos por script (form.submit() não dispara o evento "submit"):
 *  AnotAI.carregando.iniciar(elemento, 'Excluindo...') antes de enviar.
 */
(function () {
  'use strict';

  var TEMPO_LIMITE_MS = 20000;
  var ativos = [];

  function iniciar(elemento, texto) {
    if (!elemento || elemento.dataset.carregando === '1') return;
    elemento.dataset.carregando = '1';
    elemento.dataset.rotuloOriginal = elemento.innerHTML;
    elemento.dataset.larguraOriginal = elemento.style.minWidth || '';
    // segura a largura para o botão não "pular" quando o texto muda
    elemento.style.minWidth = elemento.getBoundingClientRect().width + 'px';
    elemento.classList.add('btn-carregando');
    elemento.setAttribute('aria-disabled', 'true');
    elemento.setAttribute('aria-busy', 'true');
    elemento.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' +
      (texto || elemento.dataset.textoCarregando || 'Enviando...');
    ativos.push(elemento);
    elemento._limite = window.setTimeout(function () { restaurar(elemento); }, TEMPO_LIMITE_MS);
  }

  function restaurar(elemento) {
    if (!elemento || elemento.dataset.carregando !== '1') return;
    window.clearTimeout(elemento._limite);
    elemento.innerHTML = elemento.dataset.rotuloOriginal;
    elemento.style.minWidth = elemento.dataset.larguraOriginal;
    elemento.classList.remove('btn-carregando');
    elemento.removeAttribute('aria-disabled');
    elemento.removeAttribute('aria-busy');
    delete elemento.dataset.carregando;
    delete elemento.dataset.rotuloOriginal;
    delete elemento.dataset.larguraOriginal;
    var formulario = elemento.form || elemento.closest('form');
    if (formulario) delete formulario.dataset.enviando;
  }

  function restaurarTodos() {
    var lista = ativos.splice(0, ativos.length);
    lista.forEach(restaurar);
    // garante também formulários marcados que ficaram sem botão em carregamento
    Array.prototype.forEach.call(document.querySelectorAll('form[data-enviando]'), function (f) {
      delete f.dataset.enviando;
    });
  }

  // fase de bolha: validações que chamam preventDefault() rodam antes e cancelam o carregando
  document.addEventListener('submit', function (evento) {
    var formulario = evento.target;
    if (!(formulario instanceof HTMLFormElement) || formulario.hasAttribute('data-sem-carregando')) return;
    if (formulario.dataset.enviando === '1') { evento.preventDefault(); return; }   // duplo clique ou Enter repetido
    if (evento.defaultPrevented) return;
    var botao = evento.submitter || formulario.querySelector('[type="submit"]');
    formulario.dataset.enviando = '1';
    iniciar(botao);
  });

  // pagehide: a foto que o navegador guarda para o "voltar" já fica no estado original.
  // pageshow: garantia extra para quem volta pelo cache de navegação.
  window.addEventListener('pagehide', restaurarTodos);
  window.addEventListener('pageshow', restaurarTodos);

  window.AnotAI = window.AnotAI || {};
  window.AnotAI.carregando = { iniciar: iniciar, restaurar: restaurar, restaurarTodos: restaurarTodos };
})();
