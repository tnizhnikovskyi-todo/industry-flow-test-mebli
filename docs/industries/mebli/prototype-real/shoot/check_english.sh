#!/usr/bin/env bash
# Гейт зйомки: падає, якщо в console.log (латиниця на екрані кліпів і скриншотів сценаріїв) є англійські підписи.
# Дозволені: логіни демо-ролей у меню користувача та службові слова Odoo, яких немає в uk_UA ядра.
cd "$(dirname "$0")"
bad=$(grep -E 'латиниця' console.log | grep -vE 'латиниця на екрані: (немає|Incl)(;|$)' | sed -E 's/.*латиниця( на екрані)?: //; s/; ok.*//' | tr ',' '\n' | sed 's/^ *//' | grep -vxE 'order|client|Administrator|chief|tech|owner|store|office|salon|Incl' | sort -u | tr '\n' ' ')
if [ -n "$bad" ]; then echo "ПРОВАЛ: англійські підписи на екрані: $bad"; exit 1; fi
echo "англійських підписів немає"
