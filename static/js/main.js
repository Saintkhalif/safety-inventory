// Simple confirmation for delete actions
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default for date fields in add form
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date_issued')?.setAttribute('value', today);
    document.getElementById('last_inspected')?.setAttribute('value', today);
    
    // You can add more JavaScript functionality here as needed
});