# Dockerfile para Odoo 16.0 con módulo personalizado
FROM odoo:16.0

# Argumentos de build
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=16.0

# Metadatos
LABEL maintainer="Inventory Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.description="Odoo 16.0 with Inventory Custom Module" \
      org.label-schema.name="inventory-odoo" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF

# Configurar timezone (solo si TZ está definido)
RUN if [ -n "$TZ" ]; then \
        ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
        echo $TZ > /etc/timezone; \
    fi

# Crear directorio para addons personalizados
RUN mkdir -p /mnt/extra-addons

# Copiar módulo personalizado de inventario
COPY --chown=odoo:odoo odoo_custom_module /mnt/extra-addons/inventory_custom

# Exponer puerto de Odoo
EXPOSE 8069

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:8069/web/database/manager || exit 1

# Comando por defecto
CMD ["odoo"]
