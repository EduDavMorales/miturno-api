# tests/test_sprint1_helpers.py
"""
Tests unitarios para helpers del Sprint 1
- Permisos y decorators
- Validadores
- Responses
- Dependencies
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import date, time
from app.auth.permissions import (
    user_has_permission,
    user_has_role,
    get_user_permissions,
    assign_role,
    remove_role
)
from app.utils.validators import (
    validate_email,
    validate_phone,
    validate_date_not_past,
    validate_time_range,
    validate_precio,
    validate_duracion_minutos
)
from app.utils.responses import (
    success_response,
    error_response,
    paginated_response,
    created_response
)


# ============================================================================
# TESTS DE PERMISOS
# ============================================================================

class TestPermissions:
    """Tests para sistema de permisos"""
    
    def test_user_has_permission_valid(self, db_session: Session):
        """
        Test: usuario con permiso válido retorna True
        
        Precondiciones:
        - Usuario con ID 1 tiene permiso "turno:crear:propio"
        """
        # Arrange
        usuario_id = 1
        permission_code = "turno:crear:propio"
        
        # Act
        result = user_has_permission(usuario_id, permission_code, db_session)
        
        # Assert
        assert result is True
    
    def test_user_has_permission_invalid(self, db_session: Session):
        """
        Test: usuario sin permiso retorna False
        """
        # Arrange
        usuario_id = 1
        permission_code = "sistema:administrar:usuarios"  # No tiene este
        
        # Act
        result = user_has_permission(usuario_id, permission_code, db_session)
        
        # Assert
        assert result is False
    
    def test_user_has_role_valid(self, db_session: Session):
        """
        Test: usuario con rol válido retorna True
        
        Precondiciones:
        - Usuario con ID 1 tiene rol "CLIENTE"
        """
        # Arrange
        usuario_id = 1
        rol_nombre = "CLIENTE"
        
        # Act
        result = user_has_role(usuario_id, rol_nombre, db_session)
        
        # Assert
        assert result is True
    
    def test_assign_role_success(self, db_session: Session):
        """
        Test: asignar rol nuevo funciona correctamente
        
        Precondiciones:
        - Usuario con ID 10 existe
        - Rol "EMPLEADO" existe
        - Empresa con ID 1 existe
        """
        # Arrange
        usuario_id = 10
        rol_nombre = "EMPLEADO"
        empresa_id = 1
        
        # Act
        result = assign_role(usuario_id, rol_nombre, db_session, empresa_id)
        
        # Assert
        assert result is True
        assert user_has_role(usuario_id, rol_nombre, db_session)
    
    def test_assign_role_duplicate_raises_error(self, db_session: Session):
        """
        Test: asignar rol duplicado lanza HTTPException 409
        
        Precondiciones:
        - Usuario ya tiene rol "CLIENTE"
        """
        # Arrange
        usuario_id = 1
        rol_nombre = "CLIENTE"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            assign_role(usuario_id, rol_nombre, db_session)
        
        assert exc_info.value.status_code == 409
    
    def test_remove_role_success(self, db_session: Session):
        """
        Test: remover rol existente funciona
        """
        # Arrange
        usuario_id = 1
        rol_nombre = "CLIENTE"
        
        # Act
        result = remove_role(usuario_id, rol_nombre, db_session)
        
        # Assert
        assert result is True
        # Verificar que ya no tiene el rol activo
        assert user_has_role(usuario_id, rol_nombre, db_session) is False


# ============================================================================
# TESTS DE VALIDADORES
# ============================================================================

class TestValidators:
    """Tests para validadores genéricos"""
    
    def test_validate_email_valid(self):
        """Test: email válido pasa la validación"""
        # Arrange
        email = "usuario@ejemplo.com"
        
        # Act & Assert
        assert validate_email(email) is True
    
    def test_validate_email_invalid_format(self):
        """Test: email con formato inválido lanza HTTPException"""
        # Arrange
        email = "usuario@invalido"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_email(email)
        
        assert exc_info.value.status_code == 400
        assert "email inválido" in exc_info.value.detail.lower()
    
    def test_validate_phone_valid(self):
        """Test: teléfono argentino válido pasa"""
        # Arrange
        phone = "+54 9 11 1234-5678"
        
        # Act & Assert
        assert validate_phone(phone) is True
    
    def test_validate_phone_none_allowed(self):
        """Test: teléfono None es permitido"""
        # Act & Assert
        assert validate_phone(None) is True
    
    def test_validate_date_not_past_valid(self):
        """Test: fecha futura es válida"""
        # Arrange
        from datetime import timedelta
        fecha_futura = date.today() + timedelta(days=7)
        
        # Act & Assert
        assert validate_date_not_past(fecha_futura) is True
    
    def test_validate_date_not_past_invalid(self):
        """Test: fecha pasada lanza error"""
        # Arrange
        from datetime import timedelta
        fecha_pasada = date.today() - timedelta(days=1)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_date_not_past(fecha_pasada)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_time_range_valid(self):
        """Test: rango de tiempo válido"""
        # Arrange
        hora_inicio = time(9, 0)
        hora_fin = time(18, 0)
        
        # Act & Assert
        assert validate_time_range(hora_inicio, hora_fin) is True
    
    def test_validate_time_range_invalid(self):
        """Test: hora_fin anterior a hora_inicio lanza error"""
        # Arrange
        hora_inicio = time(18, 0)
        hora_fin = time(9, 0)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_time_range(hora_inicio, hora_fin)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_precio_valid(self):
        """Test: precio positivo es válido"""
        # Arrange
        precio = 150.50
        
        # Act & Assert
        assert validate_precio(precio) is True
    
    def test_validate_precio_invalid_zero(self):
        """Test: precio 0 o negativo lanza error"""
        # Act & Assert
        with pytest.raises(HTTPException):
            validate_precio(0)
        
        with pytest.raises(HTTPException):
            validate_precio(-10)
    
    def test_validate_duracion_valid(self):
        """Test: duración de 30 minutos es válida"""
        # Arrange
        duracion = 30
        
        # Act & Assert
        assert validate_duracion_minutos(duracion) is True
    
    def test_validate_duracion_too_short(self):
        """Test: duración menor a 5 minutos lanza error"""
        # Arrange
        duracion = 3
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_duracion_minutos(duracion)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_duracion_too_long(self):
        """Test: duración mayor a 480 minutos lanza error"""
        # Arrange
        duracion = 500
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_duracion_minutos(duracion)
        
        assert exc_info.value.status_code == 400


# ============================================================================
# TESTS DE RESPONSES
# ============================================================================

class TestResponses:
    """Tests para respuestas HTTP estandarizadas"""
    
    def test_success_response_format(self):
        """Test: formato de respuesta de éxito"""
        # Arrange
        data = {"id": 1, "nombre": "Test"}
        message = "Operación exitosa"
        
        # Act
        response = success_response(data, message)
        
        # Assert
        assert response.status_code == 200
        content = eval(response.body.decode())
        assert content["success"] is True
        assert content["message"] == message
        assert content["data"] == data
    
    def test_created_response_status(self):
        """Test: respuesta created tiene status 201"""
        # Arrange
        data = {"id": 1}
        
        # Act
        response = created_response(data)
        
        # Assert
        assert response.status_code == 201
    
    def test_error_response_format(self):
        """Test: formato de respuesta de error"""
        # Arrange
        message = "Error de validación"
        errors = {"email": "Formato inválido"}
        
        # Act
        response = error_response(message, 400, errors)
        
        # Assert
        assert response.status_code == 400
        content = eval(response.body.decode())
        assert content["success"] is False
        assert content["message"] == message
        assert "errors" in content
        assert content["errors"] == errors
    
    def test_paginated_response_format(self):
        """Test: formato de respuesta paginada"""
        # Arrange
        data = [{"id": 1}, {"id": 2}]
        total = 50
        skip = 0
        limit = 10
        
        # Act
        response = paginated_response(data, total, skip, limit)
        
        # Assert
        assert response.status_code == 200
        content = eval(response.body.decode())
        
        assert content["success"] is True
        assert len(content["data"]) == 2
        assert "pagination" in content
        
        pagination = content["pagination"]
        assert pagination["total"] == 50
        assert pagination["count"] == 2
        assert pagination["skip"] == 0
        assert pagination["limit"] == 10
        assert pagination["has_next"] is True
        assert pagination["has_previous"] is False
        assert pagination["page"] == 1
        assert pagination["total_pages"] == 5


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_session():
    """
    Fixture para sesión de BD de prueba.
    
    TODO: Configurar BD de prueba con datos mock.
    Por ahora retorna None y se debe mockear.
    """
    # En una implementación completa, aquí se crearía
    # una sesión de BD de prueba con datos de testing
    return None


# ============================================================================
# INSTRUCCIONES DE USO
# ============================================================================

"""
Para ejecutar estos tests:

1. Instalar pytest:
   pip install pytest pytest-asyncio

2. Ejecutar todos los tests:
   pytest tests/test_sprint1_helpers.py

3. Ejecutar tests específicos:
   pytest tests/test_sprint1_helpers.py::TestPermissions
   pytest tests/test_sprint1_helpers.py::TestValidators::test_validate_email_valid

4. Ejecutar con coverage:
   pip install pytest-cov
   pytest tests/test_sprint1_helpers.py --cov=app --cov-report=html

5. Ejecutar con verbose:
   pytest tests/test_sprint1_helpers.py -v

NOTA: Estos tests requieren:
- BD de prueba configurada
- Datos mock cargados
- Variables de entorno de testing

Para implementación completa, crear:
- tests/conftest.py con fixtures globales
- tests/factories.py con factories de objetos
- tests/fixtures.sql con datos de prueba
"""