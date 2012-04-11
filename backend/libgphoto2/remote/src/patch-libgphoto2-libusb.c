--- libgphoto2_port/usb/libusb.c.old	2012-04-10 22:30:02.848658700 +0100
+++ libgphoto2_port/usb/libusb.c	2012-04-10 22:36:43.825593200 +0100
@@ -187,7 +187,9 @@
 			 */ 
 			sprintf (info.path, "usb:%s,%s", bus->dirname, dev->filename);
 			/* On MacOS X we might get usb:006,002-04a9-3139-00-00. */
+			#ifndef __CYGWIN__
 			s = strchr(info.path, '-');if (s) *s='\0';
+			#endif
 			CHECK (gp_port_info_list_append (list, info));
 		}
 		bus = bus->next;
