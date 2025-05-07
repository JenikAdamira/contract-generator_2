from flask import Flask, render_template, request, send_file
from docxtpl import DocxTemplate
import io
from datetime import datetime
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Akce (více položek)
        akce_count = int(request.form["akce_count"])
        nazvy_akci = []
        cisla_akci = []

        for i in range(1, akce_count + 1):
            nazev = request.form.get(f"nazev_akce_{i}")
            cislo = request.form.get(f"cislo_akce_{i}")
            if nazev:
                nazvy_akci.append(nazev)
            if cislo:
                cisla_akci.append(cislo)

        verejna_zakazka = request.form.get("verejna_zakazka", "").strip()

        if akce_count >= 2 and verejna_zakazka:
            nazev_akce_final = verejna_zakazka
        else:
            nazev_akce_final = nazvy_akci[0] if nazvy_akci else ""

        cislo_akce_final = ", ".join(cisla_akci)

        # vice_akci – seznam textu
        vice_akci = ""
        if akce_count >= 2:
            vice_akci = "které se skládá ze dvou níže uvedených jednotlivých akcí:\n"
            for cislo, nazev in zip(cisla_akci, nazvy_akci):
                if cislo and nazev:
                    vice_akci += f"č. {cislo} {nazev}\n"

        # seznam_akci – volitelné pro budoucí použití (např. se smyčkou ve Wordu)
        seznam_akci = []
        if akce_count >= 2:
            for cislo, nazev in zip(cisla_akci, nazvy_akci):
                if cislo and nazev:
                    seznam_akci.append({"cislo": cislo, "nazev": nazev})


        # Bankovní záruka
        bz_text = (
            "Zhotovitel předložil objednateli v den podpisu smlouvy o dílo originál bankovní "
            "záruky za provedení díla podle ustanovení čl. 7 Bankovní záruka, odst. 7.1. Obchodních podmínek "
            "objednatele na zhotovení stavby ze dne 1. 1. 2024. Objednatel potvrzuje podpisem smlouvy převzetí listiny."
        ) if request.form["bz"] == "ANO" else (
            "Objednatel nežádá zhotovitele o předložení bankovní záruky za provedení díla."
        )

        # Vyhrazené položky – text nebo výmaz
        vyh_text = ""
        vyh_placeholder = ""
        vz1 = ""
        vz2 = ""
        if request.form["vyh"] == "ANO":
            vyh_text = (
                "8.7. Smluvní strany se dohodly na vyhrazené změně závazku v souladu s ustanovením § 100 odst. 1 a § 222 odst. 2 "
                "zákona č. 134/2016 Sb., o zadávání veřejných zakázek, ve znění pozdějších předpisů..."
            )
            vyh_placeholder = "Do vygenerované smlouvy vlož Souhrn vyhrazených položek"
            vz1 = "(překročitelná jen při uplatnění vyhrazených změn v čl. 8.10. smlouvy a dále v režimu zákona)"
            vz2 = "(jedná se o cenu díla před aktivací změn vyhrazených v čl. 8.10. smlouvy)"
        else:
            vyh_text = "Vymaž tento odstavec"
            vyh_placeholder = ""

        # Typ projektové dokumentace
        pd_map = {
            "zjednodusena": "zjednodušenou projektovou dokumentací",
            "provadeci": "projektovou dokumentací pro provedení stavby"
        }
        pd_text = pd_map.get(request.form["pd"], "")

        # Termín dokončení díla
        if request.form["dokonceni_typ"] == "datum":
            datum_raw = request.form["dokonceni_datum"]
            try:
                parsed = datetime.strptime(datum_raw, "%Y-%m-%d")
                datum_cz = parsed.strftime("%d.%m.%Y")
                dokonceni = f"nejpozději do {datum_cz}"
            except:
                dokonceni = f"nejpozději do {datum_raw}"
        else:
            dokonceni = request.form["dokonceni_text"]

        # Listiny
        listiny = []
        for i in range(1, int(request.form["listiny_count"]) + 1):
            val = request.form.get(f"listina_{i}")
            if val:
                listiny.append(val)

        # Negace
        negace = []
        for i in range(1, int(request.form["negace_count"]) + 1):
            val = request.form.get(f"negace_{i}")
            if val:
                negace.append(val)

        # Kontext pro šablonu
        context = {
            "nazev_akce": nazev_akce_final,
            "cislo_akce": cislo_akce_final,
            "vedouci": request.form["vedouci"],
            "dozor": request.form["dozor"],
            "zahajeni": request.form["zahajeni"],
            "bz": bz_text,
            "poj": request.form["poj"],
            "vyh_text": vyh_text,
            "vyh_placeholder": vyh_placeholder,
            "vz1": vz1,
            "vz2": vz2,
            "pd": pd_text,
            "pdrok": request.form["pdrok"],
            "pdspolecnost": request.form["pdspolecnost"],
            "pdsidlo": request.form["pdsidlo"],
            "pdproj": request.form["pdproj"],
            "dokonceni": dokonceni,
            "listiny": listiny,
            "negace": negace,
            "vice_akci": vice_akci.strip(),
        "nazev_akce": nazev_akce_final,
        "cislo_akce": cislo_akce_final,
        "vice_akci": vice_akci.strip(),
        "seznam_akci": seznam_akci,

        }

        sablona = request.form["sablona"]
        doc = DocxTemplate(sablona)
        try:
            doc.render(context)
        except Exception as e:
            print("Chyba při generování šablony:", e)
            raise

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)

        filename = f"Smlouva_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        return send_file(output, as_attachment=True, download_name=filename)

    return render_template("form.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
