import os
import importlib

MODELS_FOLDER = "models"

def run_all_models(data):
    results = {}

    print("📁 Files in models folder:", os.listdir(MODELS_FOLDER))

    for file in os.listdir(MODELS_FOLDER):
        print("➡️ Checking file:", file)

        if file.endswith(".py") and file != "__init__.py":

            module_name = file[:-3]
            print("🔄 Importing:", module_name)

            try:
                module = importlib.import_module(f"models.{module_name}")
                print("✅ Imported:", module_name)

                if hasattr(module, "run"):
                    print("🚀 Running:", module_name)

                    score = module.run(data)
                    results[module_name] = float(score)

                else:
                    print("❌ No run() in:", module_name)

            except Exception as e:
                print(f"❌ Error in {module_name}: {e}")

    print("📊 Final Results:", results)

    return results