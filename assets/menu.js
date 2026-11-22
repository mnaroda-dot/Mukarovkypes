const menuButton = document.querySelector('.menu-toggle');
const navigation = document.getElementById(menuButton.getAttribute('aria-controls'));

menuButton.addEventListener('click', () => {
  const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!isOpen));
});

menuButton.parentElement.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape' || menuButton.getAttribute('aria-expanded') !== 'true' ||
      menuButton.getClientRects().length === 0 ||
      (event.target !== menuButton && !navigation.contains(event.target))) {
    return;
  }

  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.focus();
  event.preventDefault();
});

menuButton.hidden = false;
