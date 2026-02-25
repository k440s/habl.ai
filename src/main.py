from src.hablai_core import LocalizationAI 

def main():
    print("🚀 Iniciando sistema de localización...\n")
    
    # Crear instancia del sistema
    ai = LocalizationAI()
    
    # Mostrar idiomas soportados
    ai.show_supported_languages()
    
    # Test 1: Localizar a español
    print("\n" + "="*60)
    print("TEST 1: Localización a Español")
    print("="*60)
    
    result = ai.localize_to_language(
        english_text="Welcome to our AI-powered localization platform",
        target_lang='es'
    )
    
    # Test 2: Localizar a TODOS los idiomas
    print("\n" + "="*60)
    print("TEST 2: Localización completa (8 idiomas)")
    print("="*60)
    
    all_results = ai.localize_to_all_languages(
        english_text="Thank you for choosing our service"
    )
    
    print("\n✅ TODOS LOS TESTS COMPLETADOS")
    print(f"   Archivos generados: {len(all_results)} audios MP3")
    print(f"   Ubicación: ./output_audio/")

if __name__ == "__main__":
    main()