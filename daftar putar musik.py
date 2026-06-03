import os           # untuk membaca folder dan file di laptop
import pygame       # library untuk memutar musik
import threading    # untuk menjalankan 2 proses sekaligus (putar musik + terima input)

# SETUP AWAL PYGAME 
pygame.init()                               # menyalakan semua modul pygame
pygame.mixer.init()                         # menyalakan modul khusus audio

# Membuat "sinyal" khusus yang dikirim pygame saat lagu selesai diputar
LAGU_HABIS = pygame.USEREVENT + 1                       # angka unik sebagai kode sinyal
pygame.mixer.music.set_endevent(LAGU_HABIS)             # mendaftarkan sinyal ke pygame

# Representasi satu lagu sebagai NODE dalam Double Linked List
# Setiap node punya pointer ke lagu sebelumnya (prev) dan sesudahnya (next)
class Lagu:
    def __init__(self, judul, file):
        self.judul = judul      # nama lagu (string)
        self.file  = file       # lokasi file .mp3 di komputer (string path)
        self.next  = None       # pointer ke lagu sesudahnya (default kosong)
        self.prev  = None       # pointer ke lagu sebelumnya (default kosong)

# Kumpulan lagu yang disusun sebagai Double Linked List Circular
# "Circular" artinya lagu terakhir menyambung atau kembali ke lagu pertama
# Sehingga next dari tail = head dan prev dari head = tail
class Playlist:
    def __init__(self, nama):
        self.nama             = nama     # nama playlist (contoh: "Galau", "Romansa")
        self.head             = None     # node lagu pertama dalam linked list
        self.tail             = None     # node lagu terakhir dalam linked list
        self.current          = None     # node lagu yang sedang diputar
        self.playlist_penanda = None     # penanda posisi di playlist (terpisah dari queue)
        self.queue            = []       # antrian prioritas: lagu yang akan diputar dahulu
        self.lock             = threading.Lock()  # kunci agar queue aman diakses 2 thread

    # Menambahkan node lagu baru ke bagian akhir linked list
    # Setelah ditambah, sambungan circular akan diperbarui agar tetap melingkar
    def tambah_lagu(self, judul, file):
        baru = Lagu(judul, file)            # buat node lagu baru

        if self.head is None:
            # Playlist masih kosong, lagu pertama jadi head sekaligus tail
            self.head = self.tail = baru    # head dan tail sama-sama menunjuk ke lagu ini
            baru.next = baru                # next menunjuk ke diri sendiri (circular)
            baru.prev = baru                # prev menunjuk ke diri sendiri (circular)
        else:
            # Playlist sudah ada isinya, menyambungkan lagu baru di posisi paling akhir
            baru.prev       = self.tail     # prev lagu baru ke tail lama
            baru.next       = self.head     # next lagu baru ke head (melingkar ke awal)
            self.tail.next  = baru          # tail lama ke sambung ke lagu baru
            self.head.prev  = baru          # head ke prevnya sekarang lagu baru (circular)
            self.tail       = baru          # update tail ke lagu baru

    # Menelusuri linked list dari head sampai balik ke head lagi (satu putaran)
    # Menampilkan nomor + judul tiap lagu, lalu mengembalikan daftarnya sebagai list
    def tampilkan_semua_lagu(self):
        if not self.head:           # jika playlist kosong, kembalikan list kosong
            return []

        daftar = []                 # list untuk menyimpan node lagu
        lagu   = self.head          # mulai penelusuran dari lagu pertama
        nomor  = 1                  # nomor urut untuk ditampilkan

        while True:
            daftar.append(lagu)                     # simpan node ke list
            print(f"{nomor}. 🎵 {lagu.judul}")      # tampilkan ke layar
            lagu  = lagu.next                       # geser ke lagu berikutnya
            nomor += 1                              # tambah nomor urut
            if lagu == self.head:                   # jika sudah balik ke awal maka berhenti
                break

        return daftar       # kembalikan list node untuk dipakai fungsi lain

    # Menampilkan daftar lagu, lalu meminta user memilih nomor
    # Setelah dipilih, langsung memutar lagu tersebut
    def pilih_dan_putar(self):
        daftar = self.tampilkan_semua_lagu()    # tampilkan daftar dan simpan hasilnya

        while True:
            pilihan = input("\nPilih nomor lagu: ")     # minta input dari user

            if not pilihan.isdigit():                   # cek apakah input adalah angka
                print("Masukkan angka ya!")
                continue

            index = int(pilihan) - 1                    # ubah ke index (mulai dari 0)

            if 0 <= index < len(daftar):                # cek apakah index valid
                self.current          = daftar[index]    # set lagu aktif
                self.playlist_penanda = daftar[index]    # set penanda playlist di posisi yang sama
                with self.lock:
                    self.queue.clear()                  # reset antrian saat pilih lagu baru
                self.putar()                            # mulai putar lagu
                return                                  # keluar dari loop
            else:
                print("Nomor lagu tidak ada!")

    # Menampilkan daftar lagu dan meminta user memilih, tapi TIDAK langsung memutar
    # Dipakai saat ganti playlist —> user pilih lagu dulu, play belum mulai
    # Kembali True jika berhasil dipilih, False jika user batal (input 0)
    def pilih_lagu(self):
        daftar = self.tampilkan_semua_lagu()    # tampilkan daftar lagu
        print("0. Batal")

        while True:
            pilihan = input("\nPilih nomor lagu yang ingin diputar: ")

            if pilihan == "0":                          # user batal ganti playlist
                return False

            if not pilihan.isdigit():
                print("Masukkan angka ya!")
                continue

            index = int(pilihan) - 1

            if 0 <= index < len(daftar):
                self.current          = daftar[index]   # set lagu aktif (belum diputar)
                self.playlist_penanda = daftar[index]   # set penanda playlist
                with self.lock:
                    self.queue.clear()                  # reset antrian
                print(f"\n✅ Lagu yang dipilih  : {self.current.judul}")
                print(f"📁 Playlist           : {self.nama}")
                return True                             # berhasil pilih, belum play
            else:
                print("Nomor lagu tidak ada!")

    # Memuat file .mp3 dari lagu yang sedang aktif lalu memutarnya
    def putar(self):
        if self.current:                                        # pastikan ada lagu aktif
            print(f"\n▶ Memutar: {self.current.judul}")
            pygame.mixer.music.load(self.current.file)          # muat file ke pygame
            pygame.mixer.music.play()                           # mulai putar

    # Menentukan lagu apa yang diputar selanjutnya dengan 2 prioritas:
    # PRIORITAS 1: mengambil dari antrian (queue) jika ada
    # PRIORITAS 2: dilanjut ke lagu berikutnya di playlist (circular)
    def lagu_berikutnya(self):
        with self.lock:                             # kunci agar aman dari 2 thread

            if self.queue:
                # Ada antrian: mengambil lagu pertama dari antrian (pop dari depan)
                self.current = self.queue.pop(0)
                print(f"▶ Dari antrian: {self.current.judul}")

            else:
                # Antrian kosong: maju satu langkah di playlist
                # Circular: jika ini lagu terakhir, next-nya = lagu pertama
                self.playlist_penanda = self.playlist_penanda.next    # geser penanda playlist
                self.current         = self.playlist_penanda          # set sebagai lagu aktif
                print(f"▶ Memutar: {self.current.judul}")

        pygame.mixer.music.load(self.current.file)  # muat file lagu berikutnya
        pygame.mixer.music.play()                   # langsung putar

    # Mundur satu langkah ke lagu sebelumnya di playlist
    # Antrian tidak direset agar tetap tersimpan
    def lagu_sebelumnya(self):
        with self.lock:                                            # kunci thread
            self.playlist_penanda = self.playlist_penanda.prev       # mundur satu langkah (circular)
            self.current          = self.playlist_penanda            # set sebagai lagu aktif

        print(f"◀ Kembali ke: {self.current.judul}")
        pygame.mixer.music.load(self.current.file)      # muat file lagu sebelumnya
        pygame.mixer.music.play()                       # langsung putar

    # Memungkinkan user memilih lagu dari playlist yang SAMA untuk dimasukkan antrian
    # Lagu di antrian akan diputar lebih dulu sebelum melanjutkan playlist aktif
    # Circular hanya berlaku di dalam playlist ini, tidak bisa lintas playlist
    def tambah_ke_antrian(self):
        print(f"\n--- TAMBAH KE ANTRIAN [📁 {playlist_aktif.nama}] ---")
        daftar = self.tampilkan_semua_lagu()    # tampilkan lagu di playlist yang sedang aktif
        print(f"\n0. Kembali")

        while True:
            pilihan = input("\nMau tambah lagu nomor berapa ke antrian? ")

            if pilihan == "0":
                return                          # keluar dari menu antrian

            elif pilihan.isdigit():
                index = int(pilihan) - 1        # ubah ke index, kurangi 1 karena list Python mulai dari 0
                if 0 <= index < len(daftar):
                    lagu_dipilih = daftar[index]            # ambil node lagu yang dipilih
                    with self.lock:
                        self.queue.append(lagu_dipilih)     # masukkan ke ujung antrian
                    print(f"\n✅ Ditambah ke antrian")
                    print(f"   📁 Playlist : {self.nama}")
                    print(f"   🎵 Lagu     : {lagu_dipilih.judul}")
                else:
                    print("Nomor lagu tidak ada!")
            else:
                print("Masukkan angka ya!")

    def lihat_antrian(self):
    # Menampilkan urutan putar lengkap:
    # 1. Lagu yang sedang diputar
    # 2. Lagu di antrian prioritas (jika ada)
    # 3. Sisa lagu di playlist sesuai urutan circular

        print(f"\n--- ANTRIAN LAGU [📁 {playlist_aktif.nama}] ---")  # judul menu
        with self.lock:                   # kunci thread agar aman saat akses queue

            # Jika belum ada lagu aktif
            if not self.current:
                print("Tidak ada lagu.")
                return

            # Ambil semua lagu dari playlist
            # Sekaligus mempertahankan urutan asli playlist
            daftar = self.tampilkan_semua_lagu()

            # Cari posisi (index) lagu yang sedang diputar
            # +1 nanti agar nomor mulai dari 1, bukan 0
            current_index = daftar.index(self.current)

            # Tampilkan lagu yang sedang diputar
            print(
                f"\n▶ {current_index + 1}. "
                f"{self.current.judul} (Sedang diputar)"
            )

            # Jika ada lagu di antrian prioritas
            if self.queue:
                print("\n📌 Antrian Prioritas:")

                # Telusuri semua lagu dalam queue
                for lagu in self.queue:

                    # Cari nomor asli lagu di playlist
                    idx = daftar.index(lagu) + 1

                    # Tampilkan lagu antrian
                    print(f"{idx}. 🎵 {lagu.judul}")

            # Menampilkan urutan circular playlist berikutnya
            print("\nLagu yang akan diputar selanjutnya:")

            # Mulai dari lagu setelah penanda playlist
            lagu = self.playlist_penanda.next

            # Loop terus sampai kembali ke lagu aktif
            # Artinya sudah satu putaran penuh circular
            while lagu != self.current:

                # Jangan tampilkan lagu yang sudah ada di queue
                if lagu not in self.queue:

                    # Cari nomor asli lagu di playlist
                    idx = daftar.index(lagu) + 1

                    # Tampilkan lagu berikutnya
                    print(f"{idx}. 🎵 {lagu.judul}")

                # Geser ke lagu berikutnya (circular)
                lagu = lagu.next

# Berjalan di thread terpisah (background)
# Tugasnya: mendengarkan sinyal LAGU_HABIS dari pygame
# Jika sinyal diterima otomatis putar lagu berikutnya
def auto_lanjut(playlist_ref):
    global program_jalan, playlist_aktif       # akses variabel global

    while program_jalan:                        # terus jalan selama program belum ditutup
        for event in pygame.event.get():        # cek semua event yang masuk dari pygame
            if event.type == LAGU_HABIS:        # jika sinyal lagu habis diterima
                playlist_aktif.lagu_berikutnya()  # otomatis lanjut di playlist yang aktif saat ini

        pygame.time.wait(100)                   # jeda 0.1 detik agar CPU tidak terbebani

# Menyimpan semua playlist dalam bentuk dictionary
# Struktur: { "nama_folder": objek_Playlist }
# Divisualisasikan seperti struktur pohon folder
class TreePlaylist:
    def __init__(self):
        self.playlists = {}     # dictionary untuk menyimpan semua playlist

    # Jika playlist belum ada maka buat playlist baru dulu
    # Lalu tambahkan lagu ke playlist tersebut
    def tambah_lagu(self, nama_playlist, judul, file):
        if nama_playlist not in self.playlists:                         # playlist belum ada
            self.playlists[nama_playlist] = Playlist(nama_playlist)     # buat playlist baru
        self.playlists[nama_playlist].tambah_lagu(judul, file)          # tambah lagu ke playlist

    # Menampilkan semua playlist dan isinya seperti struktur pohon folder di terminal
    def tampilkan_struktur(self):
        print("\n📁 music")
        total  = len(self.playlists)    # total jumlah playlist
        urutan = 0                      # penghitung untuk menentukan simbol cabang

        for nama, playlist in self.playlists.items():
            urutan += 1
            # Simbol └── untuk item terakhir, ├── untuk yang lainnya
            simbol = "└──" if urutan == total else "├──"
            print(f"│   {simbol} 📁 {nama}")

            if playlist.head:               # jika playlist punya lagu
                lagu  = playlist.head
                semua = []

                while True:
                    semua.append(lagu.judul)    # kumpulkan semua judul
                    lagu = lagu.next
                    if lagu == playlist.head:   # berhenti saat kembali ke awal (circular)
                        break

                # Jika ini playlist terakhir, gunakan spasi kosong agar garis tidak menggantung.
                # Jika bukan playlist terakhir, tetap gunakan garis vertikal '│'.
                garis_induk = "    " if urutan == total else "│   "

                for i, judul in enumerate(semua):
                    simbol_lagu = "└──" if i == len(semua) - 1 else "├──"
                    # Menggunakan variabel garis_induk yang dinamis
                    print(f"│   {garis_induk}{simbol_lagu} 🎵 {judul}")

    # Menampilkan semua playlist dan meminta user memilih salah satu
    # Mengembalikan objek Playlist yang dipilih
    def pilih_playlist(self):
        daftar = list(self.playlists.keys())    # ambil semua nama playlist

        while True:
            print("\n--- PILIH PLAYLIST ---")
            for i, nama in enumerate(daftar, start=1):
                print(f"{i}. 📁 {nama}")

            pilihan = input("\nPilih nomor playlist: ")

            if not pilihan.isdigit():           # validasi input harus angka
                print("Masukkan angka ya!")
                continue

            index = int(pilihan) - 1                # ubah ke index, kurangi 1 karena list Python mulai dari 0
            if 0 <= index < len(daftar):
                return self.playlists[daftar[index]]    # kembalikan objek Playlist
            else:
                print("Nomor playlist tidak ada!")

# MAIN PROGRAM
# Alur utama: baca folder -> tampilkan -> pilih playlist -> pilih lagu -> kontrol
tree   = TreePlaylist()     # buat objek tree untuk menyimpan semua playlist
folder = "music"            # nama folder utama yang berisi subfolder playlist

# Telusuri semua subfolder di dalam folder "music"
for root, dirs, files in os.walk(folder):
    if root == folder:
        continue                                        # skip folder utama itu sendiri

    nama_playlist = os.path.basename(root)              # nama subfolder = nama playlist

    for file in files:
        if file.endswith(".mp3"):                       # hanya proses file .mp3
            path  = os.path.join(root, file)            # gabungkan path lengkap
            judul = file.replace(".mp3", "")            # judul = nama file tanpa ekstensi
            tree.tambah_lagu(nama_playlist, judul, path)    # masukkan ke tree

# Tampilkan struktur folder, lalu minta user pilih playlist dan lagu
tree.tampilkan_struktur()
playlist_aktif = tree.pilih_playlist()  # user pilih playlist -> simpan objek Playlist-nya
playlist_aktif.pilih_dan_putar()        # user pilih lagu -> langsung diputar

# Jalankan auto_lanjut di thread terpisah agar tidak menghalangi input user
program_jalan = True
thread_auto   = threading.Thread(target=auto_lanjut, args=(playlist_aktif,), daemon=True)
thread_auto.start()                     # mulai thread background

# Terus tampilkan menu dan tunggu input user selama program berjalan
while program_jalan:
    print(f"\n--- KONTROL [📁 {playlist_aktif.nama}] ---")
    print("1. Skip (Lagu Berikutnya)")
    print("2. Kembali (Lagu Sebelumnya)")
    print("3. Tambah ke Antrian (Play Next)")
    print("4. Lihat Antrian")
    print("5. Ganti Playlist")
    print("0. Keluar")

    pilihan = input("Pilih: ")

    if pilihan == "1":
        playlist_aktif.lagu_berikutnya()            # skip ke lagu berikutnya

    elif pilihan == "2":
        playlist_aktif.lagu_sebelumnya()            # kembali ke lagu sebelumnya

    elif pilihan == "3":
        playlist_aktif.tambah_ke_antrian()          # buka menu tambah antrian (playlist sama)

    elif pilihan == "4":
        playlist_aktif.lihat_antrian()              # tampilkan urutan putar

    elif pilihan == "5":
        # Ganti playlist: pilih playlist baru -> pilih lagu -> tapi BELUM diputar
        # Musik lama masih jalan sampai user benar-benar konfirmasi pilihan lagu
        playlist_baru = tree.pilih_playlist()           # user pilih playlist baru

        if playlist_baru.pilih_lagu():     # user pilih lagu (bisa batal dengan 0)
            pygame.mixer.music.stop()          # baru stop musik setelah lagu dipilih
            pygame.event.clear(LAGU_HABIS)
            playlist_aktif = playlist_baru     # resmi ganti playlist aktif
            playlist_aktif.putar()             # langsung putar lagu yang dipilih                            

    elif pilihan == "0":
        program_jalan = False               # hentikan loop dan thread background
        pygame.mixer.music.stop()           # stop musik
        print("\nSampai jumpa 👋")
