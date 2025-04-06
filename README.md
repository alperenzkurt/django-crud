# Uçak Üretim Django Uygulaması

Uçak üretim yönetimi için bir Django uygulaması.

## Docker Kurulumu

Bu uygulama Docker ve Docker Compose kullanılarak konteynerize edilmiştir.

### Gereksinimler

- Docker
- Docker Compose

### Uygulamayı Çalıştırma

1. Depoyu klonlayın:
   ```
   git clone https://github.com/alperenzkurt/django-crud.git
   cd django-crud
   ```

2. Konteynerleri oluşturun ve başlatın:
   ```
   docker-compose up -d --build
   ```

3. Uygulama http://localhost:8000 adresinde erişilebilir olacaktır

### Geliştirme İş Akışı

- Django yönetim komutlarını çalıştırmak için:
  ```
  docker-compose exec web python manage.py <command>
  ```

- Logları görüntülemek için:
  ```
  docker-compose logs -f
  ```

- Uygulamayı durdurmak için:
  ```
  docker-compose down
  ```

- Uygulamayı durdurmak ve birimleri kaldırmak için:
  ```
  docker-compose down -v
  ```

## Testleri Çalıştırma

### Django'nun Test Çalıştırıcısını Kullanma

Tüm testleri çalıştırın:
```
docker-compose exec web python manage.py test apps
```

Belirli bir uygulama için testleri çalıştırın:
```
docker-compose exec web python manage.py test apps.accounts
docker-compose exec web python manage.py test apps.parts
docker-compose exec web python manage.py test apps.assembly
docker-compose exec web python manage.py test apps.planes
```
