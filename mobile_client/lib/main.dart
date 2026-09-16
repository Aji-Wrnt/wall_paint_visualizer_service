import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:gal/gal.dart';

void main() {
  runApp(const MaterialApp(
    home: VisualizerScreen(),
    debugShowCheckedModeBanner: false,
  ));
}

class BoxItem {
  int id;
  bool isWall;
  Color color;
  Rect rect; // Posisi dan ukuran kotak di layar

  BoxItem({
    required this.id,
    required this.isWall,
    required this.color,
    required this.rect,
  });

  String get hexString =>
      '#${color.value.toRadixString(16).substring(2).toUpperCase()}';
}

class VisualizerScreen extends StatefulWidget {
  const VisualizerScreen({super.key});

  @override
  State<VisualizerScreen> createState() => _VisualizerScreenState();
}

class _VisualizerScreenState extends State<VisualizerScreen> {
  final ImagePicker _picker = ImagePicker();
  File? _imageFile;
  final List<BoxItem> _boxes = [];
  Color _selectedColor = const Color(0xFF3498DB);
  bool _isWall = true;
  bool _isLoading = false;

  // Ganti dengan IP Address Laptop kamu saat testing via Wi-Fi lokal
  String serverUrl = "http://192.168.1.100:8000/api/v1/process-multi-objects";

  // Data Hasil
  Uint8List? _resultImageBytes;
  List<dynamic>? _reports;

  final GlobalKey _imageKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    // Default: langsung tawarkan ambil foto dari kamera saat app dibuka
    WidgetsBinding.instance.addPostFrameCallback((_) => _pickImage(ImageSource.camera));
  }

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(source: source);
    if (picked != null) {
      setState(() {
        _imageFile = File(picked.path);
        _boxes.clear();
        _resultImageBytes = null;
        _reports = null;
      });
    }
  }

  void _addNewBox() {
    if (_imageFile == null) return;
    setState(() {
      _boxes.add(BoxItem(
        id: _boxes.length + 1,
        isWall: _isWall,
        color: _selectedColor,
        rect: const Rect.fromLTWH(60, 60, 160, 160),
      ));
    });
  }

  void _openColorPicker() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Pilih Warna Target"),
        content: SingleChildScrollView(
          child: ColorPicker(
            pickerColor: _selectedColor,
            onColorChanged: (c) => setState(() => _selectedColor = c),
            pickerAreaHeightPercent: 0.8,
          ),
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Pilih"),
          )
        ],
      ),
    );
  }

  Future<void> _processVisualization() async {
    if (_imageFile == null || _boxes.isEmpty) return;

    final renderBox = _imageKey.currentContext?.findRenderObject() as RenderBox?;
    if (renderBox == null) return;
    final displaySize = renderBox.size;

    // Decode dimensi asli gambar
    final decodedImg = await decodeImageFromList(await _imageFile!.readAsBytes());
    final scaleX = decodedImg.width / displaySize.width;
    final scaleY = decodedImg.height / displaySize.height;

    setState(() => _isLoading = true);

    try {
      final request = http.MultipartRequest("POST", Uri.parse(serverUrl));
      request.files.add(await http.MultipartFile.fromPath("file", _imageFile!.path));

      final boxesPayload = _boxes.map((b) {
        return {
          "id": b.id,
          "is_wall": b.isWall,
          "target_hex": b.hexString,
          "box": [
            (b.rect.left * scaleX).round(),
            (b.rect.top * scaleY).round(),
            (b.rect.right * scaleX).round(),
            (b.rect.bottom * scaleY).round(),
          ]
        };
      }).toList();

      request.fields["boxes_data"] = jsonEncode(boxesPayload);

      final response = await request.send();
      final respStr = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final data = jsonDecode(respStr);
        final base64Img = (data["processed_image_base64"] as String).split(',')[1];
        setState(() {
          _resultImageBytes = base64Decode(base64Img);
          _reports = data["reports"];
        });
        _showResultModal();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error Server: $respStr")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Koneksi gagal: $e")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showResultModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.85,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        expand: false,
        builder: (_, scrollController) => ListView(
          controller: scrollController,
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Hasil Visualisasi & Estimasi",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                IconButton(
                  icon: const Icon(Icons.download),
                  tooltip: "Simpan ke Galeri HP",
                  onPressed: () async {
                    if (_resultImageBytes != null) {
                      final tempDir = await getTemporaryDirectory();
                      final file = File('${tempDir.path}/recolor_result_${DateTime.now().millisecondsSinceEpoch}.jpg');
                      await file.writeAsBytes(_resultImageBytes!);
                      await Gal.putImage(file.path);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("Gambar berhasil disimpan ke Galeri!")),
                        );
                      }
                    }
                  },
                )
              ],
            ),
            const SizedBox(height: 12),
            if (_resultImageBytes != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: Image.memory(_resultImageBytes!),
              ),
            const SizedBox(height: 16),
            const Text("Rincian Objek & Resep Campuran Cat:",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (_reports != null)
              ..._reports!.map((rep) {
                final hex = rep["chosen_hex"];
                final isWall = rep["is_wall"] == true;
                final mat = rep["material_estimation"];
                final recipes = rep["paint_recipes"] as List<dynamic>?;

                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    side: BorderSide(color: Color(int.parse("0xFF${hex.replaceAll('#', '')}")), width: 2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Objek #${rep["object_id"]} (${isWall ? 'Dinding' : 'Benda'}) - $hex",
                            style: const TextStyle(fontWeight: FontWeight.bold)),
                        if (isWall && mat != null) ...[
                          const Divider(),
                          Text("📏 Ukuran: ${mat["estimated_width_m"]}m x ${mat["estimated_height_m"]}m (${mat["estimated_area_m2"]} m²)"),
                          Text("🪣 Kebutuhan: ${mat["paint_needed_ml"]} mL / ${mat["paint_needed_liters"]} Liter (${mat["recommended_cans"]})"),
                        ],
                        if (recipes != null && recipes.isNotEmpty) ...[
                          const Divider(),
                          Text("🎨 Resep: ${recipes[0]["name"]}", style: const TextStyle(fontWeight: FontWeight.w600)),
                          ...((recipes[0]["components"] as List<dynamic>).map((c) =>
                              Text(" • ${c["paint"]}: ${c["percentage"]}%", style: const TextStyle(fontSize: 13)))),
                        ]
                      ],
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AI Paint & Object Visualizer"),
        backgroundColor: Colors.blueAccent,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: "Set Server URL",
            onPressed: () {
              final ctrl = TextEditingController(text: serverUrl);
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text("IP Server Laptop"),
                  content: TextField(controller: ctrl),
                  actions: [
                    TextButton(
                      onPressed: () {
                        setState(() => serverUrl = ctrl.text);
                        Navigator.pop(ctx);
                      },
                      child: const Text("Simpan"),
                    )
                  ],
                ),
              );
            },
          )
        ],
      ),
      body: Column(
        children: [
          // Kontrol Baris Atas
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                ElevatedButton.icon(
                  onPressed: _openColorPicker,
                  icon: Container(
                    width: 18,
                    height: 18,
                    decoration: BoxDecoration(color: _selectedColor, shape: BoxShape.circle),
                  ),
                  label: const Text("Warna"),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text("Dinding"),
                  selected: _isWall,
                  onSelected: (v) => setState(() => _isWall = true),
                ),
                const SizedBox(width: 4),
                ChoiceChip(
                  label: const Text("Benda"),
                  selected: !_isWall,
                  onSelected: (v) => setState(() => _isWall = false),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.undo, color: Colors.orange),
                  tooltip: "Undo Kotak",
                  onPressed: _boxes.isEmpty
                      ? null
                      : () => setState(() {
                            _boxes.removeLast();
                            for (int i = 0; i < _boxes.length; i++) {
                              _boxes[i].id = i + 1;
                            }
                          }),
                ),
                IconButton(
                  icon: const Icon(Icons.delete_forever, color: Colors.red),
                  tooltip: "Clear Semua",
                  onPressed: _boxes.isEmpty ? null : () => setState(() => _boxes.clear()),
                ),
              ],
            ),
          ),

          // Area Gambar Interaktif
          Expanded(
            child: Center(
              child: _imageFile == null
                  ? const Text("Belum ada foto. Gunakan tombol kamera di bawah.")
                  : LayoutBuilder(
                      builder: (context, constraints) {
                        return Stack(
                          key: _imageKey,
                          children: [
                            Image.file(
                              _imageFile!,
                              fit: BoxFit.contain,
                            ),
                            ..._boxes.map((box) => ResizableBoxWidget(
                                  boxItem: box,
                                  onUpdate: (newRect) => setState(() => box.rect = newRect),
                                )),
                          ],
                        );
                      },
                    ),
            ),
          ),

          // Bottom Bar (Aksi Jepret, Tambah Kotak, Proses)
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.grey[100],
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                IconButton(
                  icon: const Icon(Icons.camera_alt, size: 28),
                  tooltip: "Ambil Foto Baru",
                  onPressed: () => _pickImage(ImageSource.camera),
                ),
                IconButton(
                  icon: const Icon(Icons.photo_library, size: 28),
                  tooltip: "Pilih dari Galeri",
                  onPressed: () => _pickImage(ImageSource.gallery),
                ),
                ElevatedButton.icon(
                  onPressed: _imageFile == null ? null : _addNewBox,
                  icon: const Icon(Icons.add_box),
                  label: const Text("Tambah Kotak"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white),
                ),
                ElevatedButton.icon(
                  onPressed: (_imageFile == null || _boxes.isEmpty || _isLoading)
                      ? null
                      : _processVisualization,
                  icon: _isLoading
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.auto_awesome),
                  label: const Text("Proses"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// Widget Kotak yang bisa di-Drag dan di-Resize ujungnya
class ResizableBoxWidget extends StatefulWidget {
  final BoxItem boxItem;
  final Function(Rect) onUpdate;

  const ResizableBoxWidget({super.key, required this.boxItem, required this.onUpdate});

  @override
  State<ResizableBoxWidget> createState() => _ResizableBoxWidgetState();
}

class _ResizableBoxWidgetState extends State<ResizableBoxWidget> {
  late double left;
  late double top;
  late double width;
  late double height;

  @override
  void initState() {
    super.initState();
    left = widget.boxItem.rect.left;
    top = widget.boxItem.rect.top;
    width = widget.boxItem.rect.width;
    height = widget.boxItem.rect.height;
  }

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: left,
      top: top,
      width: width,
      height: height,
      child: Stack(
        children: [
          // Body Kotak (Bisa di-Drag/Pindah Posisi)
          GestureDetector(
            onPanUpdate: (details) {
              setState(() {
                left += details.delta.dx;
                top += details.delta.dy;
                widget.onUpdate(Rect.fromLTWH(left, top, width, height));
              });
            },
            child: Container(
              decoration: BoxDecoration(
                border: Border.all(color: widget.boxItem.color, width: 3),
                color: widget.boxItem.color.withOpacity(0.2),
              ),
              child: Align(
                alignment: Alignment.topLeft,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  color: widget.boxItem.color,
                  child: Text(
                    "#${widget.boxItem.id} ${widget.boxItem.isWall ? 'Dinding' : 'Benda'}",
                    style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ),

          // Handle Resize di Pojok Kanan Bawah
          Positioned(
            right: 0,
            bottom: 0,
            child: GestureDetector(
              onPanUpdate: (details) {
                setState(() {
                  width = (width + details.delta.dx).clamp(40.0, 400.0);
                  height = (height + details.delta.dy).clamp(40.0, 400.0);
                  widget.onUpdate(Rect.fromLTWH(left, top, width, height));
                });
              },
              child: Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: widget.boxItem.color,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.open_in_full, size: 14, color: Colors.white),
              ),
            ),
          ),
        ],
      ),
    );
  }
}