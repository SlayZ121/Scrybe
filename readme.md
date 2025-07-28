### Task 1A: Run the PDF Processor

After cloning the repository:

```bash
git clone <url>
```

---

### 🐳 Build the Docker Image

```bash
docker build --platform=linux/amd64 -t mysolutionname:docsage .
```

---

### ▶️ Run the Container

#### 🪟 On Windows (PowerShell):

```powershell
docker run --rm `
  -v "${PWD}\input:/app/input" `
  -v "${PWD}\output:/app/output" `
  --network none `
  mysolutionname:docsage
```

#### 🐧 On Linux / macOS:

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  mysolutionname:docsage
```

---

### 📤 Output

This will automatically process all PDF files in the `input/` folder and save the resulting JSON files into the `output/` folder.

Each processed file will have its corresponding JSON representation stored under `/output`.
