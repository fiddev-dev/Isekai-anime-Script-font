# Isekai Script Fonts (Open Source)

Welcome to the **Isekai Script Fonts** repository! This is an open-source project containing custom TrueType Fonts (TTF) and raw character glyph images inspired by various fictional languages and writing systems from popular Isekai and fantasy anime series.

These fonts are perfect for web applications, fan projects, decoding games, or subtitle overlays.

---

## 🎨 Available Fonts & Preview Details

The following fictional scripts are currently included in this repository:

| Font Family Name | Output Filename (`.ttf`) | Source Anime / Universe | Supported Glyphs | Case Sensitivity |
| :--- | :--- | :--- | :--- | :--- |
| **Ancient Elvish Frieren** | `ancient-elvish-frieren.ttf` | *Frieren: Beyond Journey's End* | `A-Z`, `a-z`, `0-9` | Yes (Dual-case support) |
| **Hamefura Alphabet** | `Hamefura_alphabetb-1024x856.ttf` | *My Next Life as a Villainess* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Dashert Language Alphabet** | `dashert_languange_alfabet.ttf` | *Dashert / Fantasy* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Fontaine Language Alphabet** | `fontaine_languange_alfabet.ttf` | *Genshin Impact (Fontaine)* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Konosuba Alphabet** | `konosuba-alphabet.ttf` | *KonoSuba: God's Blessing on this Wonderful World!* | `A-Z`, `a-z` | Yes (Dual-case support) |
| **Mushoku Tensei Alphabet** | `mushoku_tensei_alphabet.ttf` | *Mushoku Tensei: Jobless Reincarnation* | `A-Z`, `a-z` | Yes (Dual-case support) |
| **Overlord Alphabet** | `overlord_alphabet.ttf` | *Overlord* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Rezero Alphabet** | `rezero_alphabet.ttf` | *Re:Zero − Starting Life in Another World* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Sumeru Language Alphabet** | `sumeru_languange_alfabet.ttf` | *Genshin Impact (Sumeru)* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Tate No Yusha Alphabet** | `tate-no-yusha-alphabet.ttf` | *The Rising of the Shield Hero* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Teyvat Language Alphabet** | `teyvat_languange_alfabet.ttf` | *Genshin Impact (Teyvat)* | `A-Z`, `a-z` | Case-insensitive (mapped same) |
| **Zozan Runes** | `Zozan_runes-Regular_by_simon _secretsneakyalt.ttf` | - | `A-Z`, `a-z` | Yes (Dual-case support) |

> [!NOTE]
> *Case-insensitive* indicates that only one set of character images (usually uppercase) was provided. The compiler automatically maps these glyphs to both uppercase and lowercase codes so typing in any casing renders correctly.

---

## 🤝 How to Contribute

Contributions are welcome! If you want to add new Isekai script styles, fix contours, or optimize character spacing, follow these steps:

### How to Add a New Script:
1. **Prepare Glyph Images**:
   Create a new folder under `alfabet_image/` (e.g., `my_new_isekai_script`).
2. **Name the Files Properly**:
   The compiler maps glyphs based on filename suffixes:
   * **Uppercase:** `[Letter]_symbol.png` (e.g., `A_symbol.png`, `B_symbol.png`)
   * **Lowercase (optional):** `[Letter]_lower_symbol.png` (e.g., `A_lower_symbol.png`)
   * **Numbers (optional):** `[Digit]_symbol.png` (e.g., `0_symbol.png`)
   * **Special Symbols / Punctuation (optional):** Use unicode hex format: `uni_[unicode_hex]_symbol.png` (e.g., `uni_003f_symbol.png` for a question mark `?`).
3. **Ensure Good Quality**:
   Images should ideally be high-contrast (black outlines on a transparent or white background) and centered.
4. **Compile & Verify**:
   Run `python generate_fonts.py` and open the compiled `.ttf` file in a font viewer to verify glyph outlines and rendering.
5. **Submit a Pull Request**:
   Commit your new images folder, the compiled `.ttf` file, and update `README.md` if necessary, then create a Pull Request!

---

## ⚖️ License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.