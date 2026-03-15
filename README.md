# LaTeX Text Generator for Blender

A Blender add-on that converts LaTeX notation into 3D text objects, including mathematical equations, formatted text, and tables. Perfect for creating technical visualizations, educational content, and mathematical animations.

**[Watch Demo Video](https://youtube.com/@Katterkie)**

---

## Features

- **Self-Contained**: No external LaTeX installation or dependencies required
- **Mathematical Equations**: Full support for inline and display math modes with complex equations
- **Matrices**: Create mathematical matrices in various styles (matrix, pmatrix, bmatrix, etc.)
- **Tables**: Generate 3D tables from LaTeX tabular environment with multirow/multicolumn support
- **Text Formatting**: Bold, italic, monospace text, paragraphs, and line breaks using LaTeX commands
- **Lists & Structures**: Itemize and enumerate environments with nesting support
- **Custom Fonts**: Load and use any TrueType or OpenType fonts from your system for base, bold, and italic text
- **Customizable Output**: Control scale, thickness, spacing, and choose between individual objects or merged output

---

## Installation

1. **Download** the latest release as a ZIP file from this repository
2. **Open Blender** (version 4.2 or newer)
3. Navigate to **Edit → Preferences → Add-ons**
4. Click the **Install** button in the top-right corner
5. Browse to the downloaded `latex-addon-main.zip` file and select it
6. Click **Install Add-on**
7. Wait for the add-on to appear in the list (this may take a moment)
8. **Enable** the add-on by checking the box next to **LaTeX Text Generator**

### Accessing the Add-on

Once installed, access the add-on from the 3D Viewport:
1. Press **N** to toggle the sidebar (if not already visible)
2. Look for the **LaTeX Text** tab on the right side
3. **Important**: Ensure you're in **Object Mode** when generating text

![Accessing Add-on](https://github.com/kstrenkova/latex-addon/blob/main/img/accessing_addon.png)

---

## Usage

The add-on panel is organized into several sections that give you full control over your 3D text:

### Text Input

**Text Field**: Enter your LaTeX code here using standard LaTeX notation.
- Click the **text editor icon** on the right to open a larger text editor
- In the text editor, you can write multi-line LaTeX with better formatting
- Click **Save & Return** to apply your changes back to the main panel

![Text Editor](https://github.com/kstrenkova/latex-addon/blob/main/img/text_editor.png)

### Custom Fonts

Expand this section to use custom fonts instead of Blender's default font:

1. **Font Path**: Click the folder icon to browse and select a font file (.ttf, .otf) from your computer
2. Click `Load Font` button to load the selected font into Blender (fonts are loaded only once)
3. **Font Selection Dropdowns**:
   - **Base**: Choose the font for normal text
   - **Bold**: Choose the font for bold text (e.g., `\textbf{}`)
   - **Italic**: Choose the font for italic text (e.g., `\textit{}`)

All loaded fonts will appear in these dropdown menus for easy reuse.

### Transform Text

Adjust the appearance and spacing of your 3D text:

- **Scale**: Overall size multiplier for the output
- **Thickness**: Extrusion depth of the 3D text
- **Line Height**: Vertical spacing between lines of text
- **Word Spacing**: Horizontal spacing between words
- **Block Spacing**: Vertical spacing before paragraphs and list items

Click `Reset Parameters` button to restore all transform values to their defaults.

### Final Output

**Generate as one object**:
- **Unchecked** (default): Each character/element becomes a separate 3D object
- **Checked**: All text is merged into a single 3D object

Click `Add Text` button to create your 3D text objects in the viewport.

---

## Supported LaTeX Commands

This add-on supports a selected subset of LaTeX commands for the most common use cases.

### Text Mode

- **Font Formatting**:
  - `\textbf{text}` - Bold text
  - `\textit{text}` - Italic text
  - `\texttt{text}` - Monospace/typewriter text
- **Verbatim**: `\verb|text|` - Display text literally without interpreting LaTeX commands
- **Paragraphs**: `\par`
- **Line Breaks**: `\\` for manual line breaks
- **Math Mode Entry**:
  - Inline: `$...$`, `\(...\)`, `\begin{math}...\end{math}`
  - Display: `\[...\]`, `\begin{displaymath}...\end{displaymath}`, `\begin{equation}...\end{equation}`
- **Lists** (supports nesting):
  - `\begin{itemize}...\end{itemize}` - Bulleted lists
  - `\begin{enumerate}...\end{enumerate}` - Numbered lists
  - `\item` - List item
  - `\item[symbol]` - Custom bullet symbol

### Math Mode

- **Symbols**: Most common mathematical symbols (Greek letters, operators, relations, etc.)
- **Superscripts & Subscripts**:
  - `x^2` - Superscript
  - `x_i` - Subscript
  - `x_i^2` - Combined subscript and superscript
  - `x^{\alpha}` - Grouped superscripts
- **Spacing**: `\!`, `\,`, `\;`, `\quad`, `\qquad`
- **Roots**:
  - `\sqrt{x}` - Square root
  - `\sqrt[n]{x}` - nth root
- **Large Operators**:
  - `\sum_{lower}^{upper}` - Summation
  - `\prod_{lower}^{upper}` - Product
  - `\lim_{x \to a}` - Limit
- **Fractions**:
  - `\frac{numerator}{denominator}` - Standard fraction
  - `\dfrac{numerator}{denominator}` - Display-style fraction
- **Math Fonts** (uppercase letters only):
  - `\mathcal{X}` - Calligraphic
  - `\mathbb{R}` - Blackboard bold
  - `\mathfrak{A}` - Fraktur
- **Matrices** (supports nesting):
  - `\begin{matrix}...\end{matrix}` - Plain
  - `\begin{pmatrix}...\end{pmatrix}` - Parentheses (...)
  - `\begin{bmatrix}...\end{bmatrix}` - Brackets [...]
  - `\begin{Bmatrix}...\end{Bmatrix}` - Braces {...}
  - `\begin{vmatrix}...\end{vmatrix}` - Vertical bars |...|
  - `\begin{Vmatrix}...\end{Vmatrix}` - Double bars ||...||

### Tables (Tabular Environment)

- **Column Alignment**:
  - `l` - Left-aligned column
  - `r` - Right-aligned column
  - `c` - Center-aligned column
  - `p{width}` - Paragraph column with specified width
- **Lines**:
  - `|` in column specification - Vertical lines
  - `\hline` - Horizontal line across all columns
  - `\cline{start-end}` - Partial horizontal line
- **Cell Spanning**:
  - `\multirow{rows}{*}{content}` - Span multiple rows (auto width)
  - `\multirow{rows}{width}{content}` - Span multiple rows (fixed width)
  - `\multicolumn{cols}{alignment}{content}` - Span multiple columns

---

## Troubleshooting

If you experience any issues, check the **System Console** (**Window → Toggle System Console**) for error messages. Common issues include:

- **Add-on doesn't appear**: Wait a moment or restart Blender
- **Text doesn't generate**: Ensure you're in Object Mode and LaTeX syntax is correct
- **Font won't load**: Verify the file format is .ttf or .otf and check file permissions

---

## License

This project is open source. Feel free to use it for your Blender projects, both personal and commercial.
