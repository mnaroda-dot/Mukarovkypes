# Mukařovský pes

Statický vícestránkový web pro komunitní akci **Mukařovský pes**.

## Stav repozitáře

Repozitář je určený pro správu webu `mukarovskypes.com` přes GitHub a následné automatické nasazení přes Netlify.

Aktuální doporučený workflow:

1. Uložit webové soubory do tohoto GitHub repozitáře.
2. Připojit repozitář v Netlify.
3. Nastavit Netlify deploy z větve `main`.
4. Drobné textové změny provádět přímo přes GitHub úpravou konkrétních HTML souborů.
5. Netlify následně automaticky nasadí změny na web.

## Doporučená struktura webu

```text
index.html
informace.html
misto.html
discipliny.html
canicross.html
dogtrek.html
program.html
pravidla.html
prihlasky.html
merch.html
galerie.html
partneri.html
kontakt.html
dekujeme.html
assets/style.css
images/
```

## Nastavení pro Netlify

Pro statický HTML web není potřeba žádný build proces.

Doporučené nastavení v Netlify:

- **Build command:** nechat prázdné
- **Publish directory:** `.`
- **Production branch:** `main`

## Formuláře

Formuláře na webu jsou připravené pro Netlify Forms. Po připojení repozitáře a prvním deployi je potřeba ověřit v Netlify sekci **Forms**, že se formuláře správně detekovaly.

## Poznámka k editaci textů

Po připojení GitHubu na Netlify bude možné upravovat drobné texty přímo v GitHubu:

1. otevřít konkrétní soubor, například `galerie.html`,
2. kliknout na ikonu tužky,
3. upravit text,
4. uložit přes **Commit changes**,
5. Netlify změnu automaticky nasadí.
