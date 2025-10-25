"""
Servicio para interactuar con la API de GoHighLevel (GHL)
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_contacts(limit: int = 100) -> dict:
    """
    Obtiene la lista de contactos de GoHighLevel

    Args:
        limit: Número máximo de contactos a obtener

    Returns:
        dict: Lista de contactos con 'success', 'contacts' y 'message'
    """
    try:
        if not settings.GHL_TOKEN:
            logger.error("[GHL] GHL_TOKEN no configurado")
            return {
                "success": False,
                "contacts": [],
                "message": "GHL_TOKEN no configurado",
            }

        if not settings.GHL_BASE_URL:
            logger.error("[GHL] GHL_BASE_URL no configurado")
            return {
                "success": False,
                "contacts": [],
                "message": "GHL_BASE_URL no configurado",
            }

        if not settings.GHL_LOCATION_ID:
            logger.error("[GHL] GHL_LOCATION_ID no configurado")
            return {
                "success": False,
                "contacts": [],
                "message": "GHL_LOCATION_ID no configurado",
            }

        # Endpoint de GHL para obtener contactos
        url = f"{settings.GHL_BASE_URL.rstrip('/')}/contacts/"

        headers = {
            "Authorization": f"Bearer {settings.GHL_TOKEN}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

        params = {"locationId": settings.GHL_LOCATION_ID, "limit": limit}

        logger.info(
            f"[GHL] Obteniendo contactos del location {settings.GHL_LOCATION_ID}"
        )

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            logger.error(
                f"[GHL] Error obteniendo contactos: {response.status_code} - {response.text}"
            )
            return {
                "success": False,
                "contacts": [],
                "message": f"Error obteniendo contactos: {response.status_code}",
                "details": response.text,
            }

        data = response.json()
        contacts = data.get("contacts", [])

        # Log para debug - ver la estructura de los contactos
        if contacts and len(contacts) > 0:
            logger.info(f"[GHL] Ejemplo de contacto: {contacts[0]}")

        # Formatear contactos para el frontend
        formatted_contacts = []
        for contact in contacts:
            # Intentar obtener el nombre de diferentes campos posibles
            name = None

            # Opción 1: Campo 'name'
            if contact.get("name"):
                name = contact.get("name")
            # Opción 2: Concatenar firstName y lastName
            elif contact.get("firstName") or contact.get("lastName"):
                first = contact.get("firstName", "")
                last = contact.get("lastName", "")
                name = f"{first} {last}".strip()
            # Opción 3: Otros campos posibles
            elif contact.get("fullName"):
                name = contact.get("fullName")
            elif contact.get("fullNameLowerCase"):
                name = contact.get("fullNameLowerCase")
            elif contact.get("contactName"):
                name = contact.get("contactName")

            # Si no hay nombre, usar el email o "Sin nombre"
            if not name or name.strip() == "":
                if contact.get("email"):
                    name = contact.get("email")
                else:
                    name = "Sin nombre"

            formatted_contacts.append(
                {
                    "id": contact.get("id"),
                    "name": name,
                    "email": contact.get("email", ""),
                    "phone": contact.get("phone", ""),
                    "tags": contact.get("tags", []),
                }
            )

        logger.info(f"[GHL] Se obtuvieron {len(formatted_contacts)} contactos")

        return {
            "success": True,
            "contacts": formatted_contacts,
            "message": f"Se obtuvieron {len(formatted_contacts)} contactos",
            "total": len(formatted_contacts),
        }

    except Exception as e:
        logger.error(f"[GHL] Error inesperado obteniendo contactos: {str(e)}")
        return {
            "success": False,
            "contacts": [],
            "message": f"Error inesperado: {str(e)}",
        }


def add_tag_to_contact(contact_id: str, tag: str = "pago_confirmado") -> dict:
    """
    Agrega un tag a un contacto en GoHighLevel

    Args:
        contact_id: ID del contacto en GHL
        tag: Tag a agregar (default: "pago_confirmado")

    Returns:
        dict: Resultado de la operación con 'success' y 'message'
    """
    try:
        if not settings.GHL_TOKEN:
            logger.error("[GHL] GHL_TOKEN no configurado")
            return {"success": False, "message": "GHL_TOKEN no configurado"}

        if not settings.GHL_BASE_URL:
            logger.error("[GHL] GHL_BASE_URL no configurado")
            return {"success": False, "message": "GHL_BASE_URL no configurado"}

        if not settings.GHL_LOCATION_ID:
            logger.error("[GHL] GHL_LOCATION_ID no configurado")
            return {"success": False, "message": "GHL_LOCATION_ID no configurado"}

        # Endpoint de GHL para agregar tags a un contacto
        url = f"{settings.GHL_BASE_URL.rstrip('/')}/contacts/{contact_id}"

        headers = {
            "Authorization": f"Bearer {settings.GHL_TOKEN}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",  # GHL API version
        }

        # Log de la operación
        logger.info(
            f"[GHL] Obteniendo contacto {contact_id} del location {settings.GHL_LOCATION_ID}"
        )

        # Primero obtener los tags actuales del contacto
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(
                f"[GHL] Error obteniendo contacto {contact_id}: {response.status_code} - {response.text}"
            )
            return {
                "success": False,
                "message": f"Error obteniendo contacto: {response.status_code}",
                "details": response.text,
            }

        contact_data = response.json()
        existing_tags = contact_data.get("contact", {}).get("tags", [])

        # Verificar si el tag ya existe
        if tag in existing_tags:
            logger.info(f"[GHL] Tag '{tag}' ya existe en contacto {contact_id}")
            return {
                "success": True,
                "message": f"Tag '{tag}' ya existía en el contacto",
                "tag": tag,
                "contact_id": contact_id,
            }

        # Agregar el nuevo tag a la lista
        new_tags = existing_tags + [tag]

        # Actualizar el contacto con los nuevos tags
        payload = {"tags": new_tags}

        update_response = requests.put(url, headers=headers, json=payload)

        if update_response.status_code in [200, 201]:
            logger.info(
                f"[GHL] Tag '{tag}' agregado exitosamente al contacto {contact_id}"
            )
            return {
                "success": True,
                "message": f"Tag '{tag}' agregado exitosamente",
                "tag": tag,
                "contact_id": contact_id,
                "all_tags": new_tags,
            }
        else:
            logger.error(
                f"[GHL] Error actualizando contacto {contact_id}: {update_response.status_code} - {update_response.text}"
            )
            return {
                "success": False,
                "message": f"Error actualizando contacto: {update_response.status_code}",
                "details": update_response.text,
            }

    except requests.RequestException as e:
        logger.error(
            f"[GHL] Error de conexión al actualizar contacto {contact_id}: {str(e)}"
        )
        return {"success": False, "message": f"Error de conexión: {str(e)}"}

    except Exception as e:
        logger.error(f"[GHL] Error inesperado al agregar tag: {str(e)}")
        return {"success": False, "message": f"Error inesperado: {str(e)}"}


def update_custom_field(
    contact_id: str, field_key: str = "payment_status", field_value: str = "paid"
) -> dict:
    """
    Actualiza un custom field en un contacto de GoHighLevel

    Args:
        contact_id: ID del contacto en GHL
        field_key: Nombre del campo personalizado
        field_value: Valor a asignar

    Returns:
        dict: Resultado de la operación con 'success' y 'message'
    """
    try:
        if (
            not settings.GHL_TOKEN
            or not settings.GHL_BASE_URL
            or not settings.GHL_LOCATION_ID
        ):
            logger.error("[GHL] Credenciales GHL no configuradas completamente")
            return {
                "success": False,
                "message": "Credenciales GHL no configuradas completamente",
            }

        logger.info(
            f"[GHL] Actualizando custom field {field_key}={field_value} en contacto {contact_id}"
        )

        url = f"{settings.GHL_BASE_URL.rstrip('/')}/contacts/{contact_id}"

        headers = {
            "Authorization": f"Bearer {settings.GHL_TOKEN}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

        payload = {"customFields": [{"key": field_key, "field_value": field_value}]}

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            logger.info(
                f"[GHL] Custom field '{field_key}={field_value}' actualizado en contacto {contact_id}"
            )
            return {
                "success": True,
                "message": f"Custom field actualizado: {field_key}={field_value}",
                "contact_id": contact_id,
            }
        else:
            logger.error(
                f"[GHL] Error actualizando custom field: {response.status_code} - {response.text}"
            )
            return {
                "success": False,
                "message": f"Error actualizando custom field: {response.status_code}",
                "details": response.text,
            }

    except Exception as e:
        logger.error(f"[GHL] Error al actualizar custom field: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}
