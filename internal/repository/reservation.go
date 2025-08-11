package repository

import (
	"database/sql"
	"fmt"
	"time"

	"inventory-service/internal/models"

	"github.com/google/uuid"
)

type ReservationRepository interface {
	Create(reservation *models.Reservation) error
	GetByID(id uuid.UUID) (*models.Reservation, error)
	GetByOrderID(orderID uuid.UUID) ([]*models.Reservation, error)
	UpdateStatus(id uuid.UUID, status models.ReservationStatus) error
	GetExpiredReservations() ([]*models.Reservation, error)
	DeleteExpired(expiredBefore time.Time) error
	GetActiveReservationsForProduct(productID uuid.UUID) ([]*models.Reservation, error)
}

type reservationRepository struct {
	db *sql.DB
}

func NewReservationRepository(db *sql.DB) ReservationRepository {
	return &reservationRepository{db: db}
}

func (r *reservationRepository) Create(reservation *models.Reservation) error {
	query := `
		INSERT INTO reservations (order_id, product_id, sku, quantity, status, expires_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at, updated_at`
	
	err := r.db.QueryRow(query, reservation.OrderID, reservation.ProductID, reservation.SKU,
		reservation.Quantity, reservation.Status, reservation.ExpiresAt).
		Scan(&reservation.ID, &reservation.CreatedAt, &reservation.UpdatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to create reservation: %w", err)
	}
	
	return nil
}

func (r *reservationRepository) GetByID(id uuid.UUID) (*models.Reservation, error) {
	query := `
		SELECT r.id, r.order_id, r.product_id, r.sku, r.quantity, r.status,
			   r.expires_at, r.created_at, r.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM reservations r
		JOIN products p ON r.product_id = p.id
		WHERE r.id = $1`
	
	row := r.db.QueryRow(query, id)
	
	reservation := &models.Reservation{Product: &models.Product{}}
	err := row.Scan(
		&reservation.ID, &reservation.OrderID, &reservation.ProductID, &reservation.SKU,
		&reservation.Quantity, &reservation.Status, &reservation.ExpiresAt,
		&reservation.CreatedAt, &reservation.UpdatedAt,
		&reservation.Product.ID, &reservation.Product.SKU, &reservation.Product.Name,
		&reservation.Product.Description, &reservation.Product.Price, &reservation.Product.Category,
		&reservation.Product.IsActive, &reservation.Product.CreatedAt, &reservation.Product.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("reservation not found: %s", id)
		}
		return nil, fmt.Errorf("failed to get reservation: %w", err)
	}
	
	return reservation, nil
}

func (r *reservationRepository) GetByOrderID(orderID uuid.UUID) ([]*models.Reservation, error) {
	query := `
		SELECT r.id, r.order_id, r.product_id, r.sku, r.quantity, r.status,
			   r.expires_at, r.created_at, r.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM reservations r
		JOIN products p ON r.product_id = p.id
		WHERE r.order_id = $1
		ORDER BY r.created_at`
	
	rows, err := r.db.Query(query, orderID)
	if err != nil {
		return nil, fmt.Errorf("failed to get reservations by order ID: %w", err)
	}
	defer rows.Close()
	
	var reservations []*models.Reservation
	for rows.Next() {
		reservation := &models.Reservation{Product: &models.Product{}}
		err := rows.Scan(
			&reservation.ID, &reservation.OrderID, &reservation.ProductID, &reservation.SKU,
			&reservation.Quantity, &reservation.Status, &reservation.ExpiresAt,
			&reservation.CreatedAt, &reservation.UpdatedAt,
			&reservation.Product.ID, &reservation.Product.SKU, &reservation.Product.Name,
			&reservation.Product.Description, &reservation.Product.Price, &reservation.Product.Category,
			&reservation.Product.IsActive, &reservation.Product.CreatedAt, &reservation.Product.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan reservation: %w", err)
		}
		reservations = append(reservations, reservation)
	}
	
	return reservations, nil
}

func (r *reservationRepository) UpdateStatus(id uuid.UUID, status models.ReservationStatus) error {
	query := `UPDATE reservations SET status = $1 WHERE id = $2`
	
	result, err := r.db.Exec(query, status, id)
	if err != nil {
		return fmt.Errorf("failed to update reservation status: %w", err)
	}
	
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}
	
	if rowsAffected == 0 {
		return fmt.Errorf("reservation not found: %s", id)
	}
	
	return nil
}

func (r *reservationRepository) GetExpiredReservations() ([]*models.Reservation, error) {
	query := `
		SELECT r.id, r.order_id, r.product_id, r.sku, r.quantity, r.status,
			   r.expires_at, r.created_at, r.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM reservations r
		JOIN products p ON r.product_id = p.id
		WHERE r.expires_at < NOW() AND r.status IN ('pending', 'confirmed')
		ORDER BY r.expires_at`
	
	rows, err := r.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to get expired reservations: %w", err)
	}
	defer rows.Close()
	
	var reservations []*models.Reservation
	for rows.Next() {
		reservation := &models.Reservation{Product: &models.Product{}}
		err := rows.Scan(
			&reservation.ID, &reservation.OrderID, &reservation.ProductID, &reservation.SKU,
			&reservation.Quantity, &reservation.Status, &reservation.ExpiresAt,
			&reservation.CreatedAt, &reservation.UpdatedAt,
			&reservation.Product.ID, &reservation.Product.SKU, &reservation.Product.Name,
			&reservation.Product.Description, &reservation.Product.Price, &reservation.Product.Category,
			&reservation.Product.IsActive, &reservation.Product.CreatedAt, &reservation.Product.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan expired reservation: %w", err)
		}
		reservations = append(reservations, reservation)
	}
	
	return reservations, nil
}

func (r *reservationRepository) DeleteExpired(expiredBefore time.Time) error {
	query := `DELETE FROM reservations WHERE expires_at < $1 AND status = 'expired'`
	
	_, err := r.db.Exec(query, expiredBefore)
	if err != nil {
		return fmt.Errorf("failed to delete expired reservations: %w", err)
	}
	
	return nil
}

func (r *reservationRepository) GetActiveReservationsForProduct(productID uuid.UUID) ([]*models.Reservation, error) {
	query := `
		SELECT r.id, r.order_id, r.product_id, r.sku, r.quantity, r.status,
			   r.expires_at, r.created_at, r.updated_at
		FROM reservations r
		WHERE r.product_id = $1 AND r.status IN ('pending', 'confirmed') AND r.expires_at > NOW()
		ORDER BY r.created_at`
	
	rows, err := r.db.Query(query, productID)
	if err != nil {
		return nil, fmt.Errorf("failed to get active reservations for product: %w", err)
	}
	defer rows.Close()
	
	var reservations []*models.Reservation
	for rows.Next() {
		reservation := &models.Reservation{}
		err := rows.Scan(
			&reservation.ID, &reservation.OrderID, &reservation.ProductID, &reservation.SKU,
			&reservation.Quantity, &reservation.Status, &reservation.ExpiresAt,
			&reservation.CreatedAt, &reservation.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan active reservation: %w", err)
		}
		reservations = append(reservations, reservation)
	}
	
	return reservations, nil
}
