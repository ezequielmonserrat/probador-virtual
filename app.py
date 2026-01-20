# --- 5. BOTÓN Y GENERACIÓN ACTUALIZADO ---

st.markdown("---")

if st.button("✨ GENERAR PRUEBA AHORA"):
    if not img_prenda or not img_usuario:
        st.warning("⚠️ Faltan datos: Asegurate de cargar la prenda y tu foto.")
    else:
        with st.spinner("Procesando con Gemini Pro... Esto puede tardar unos segundos."):
            try:
                # 1. Medimos tu foto original para el re-dimensionado final
                orig_w, orig_h = img_usuario.size
                
                # 2. Prompt optimizado para evitar bloqueos de seguridad
                # Usamos términos más neutros y técnicos
                prompt = (
                    "Image-to-image editing task: Clothing transfer. "
                    "The person in the first image should wear the garment shown in the second image. "
                    "Maintain the person's pose, face, identity, and the background exactly as in the first image. "
                    "Adapt the texture and shape of the new garment to the person's body naturally. "
                    "Output the final image only."
                )

                # 3. CAMBIO DE MODELO: Usamos 1.5-pro que es más robusto para estas tareas
                response = client.models.generate_content(
                    model='gemini-1.5-pro',
                    contents=[prompt, img_usuario, img_prenda]
                )

                # Verificamos si hubo respuesta y si contiene datos
                if response and response.candidates and response.candidates[0].content.parts:
                    # 4. Procesar y redimensionar
                    generated_data = response.candidates[0].content.parts[0].inline_data.data
                    final_img = PIL.Image.open(io.BytesIO(generated_data))
                    
                    # 5. Volver al tamaño exacto de tu foto original
                    final_img = final_img.resize((orig_w, orig_h), PIL.Image.Resampling.LANCZOS)

                    st.success("¡Prueba completada con éxito!")
                    st.image(final_img, caption="Resultado Final", use_container_width=True)
                else:
                    # Si el modelo bloquea por seguridad, avisamos de forma clara
                    st.error("🔒 La IA declinó generar la imagen. Esto suele pasar con camisetas de fútbol por derechos de marca. Intentá con una prenda de color liso para probar.")

            except Exception as e:
                # Capturamos el error específico por si es falta de cuota o API
                st.error(f"Error técnico detallado: {str(e)}")
