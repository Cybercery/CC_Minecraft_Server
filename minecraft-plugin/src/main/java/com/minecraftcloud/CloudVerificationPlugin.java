package com.minecraftcloud;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.GameMode;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class CloudVerificationPlugin extends JavaPlugin implements Listener, CommandExecutor {

    private String apiUrl;
    private String apiKey;
    private boolean freeze;
    private boolean blindness;
    private final Set<UUID> unverifiedPlayers = ConcurrentHashMap.newKeySet();
    private HttpClient httpClient;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        this.apiUrl = getConfig().getString("api_url", "http://backend:8000/minecraft/plugin");
        String configuredKey = getConfig().getString("api_key", "");
        String envKey = System.getenv("PLUGIN_API_KEY");
        if (envKey != null && !envKey.trim().isEmpty()) {
            this.apiKey = envKey.trim();
        } else {
            this.apiKey = configuredKey;
        }
        this.freeze = getConfig().getBoolean("unverified_freeze", true);
        this.blindness = getConfig().getBoolean("unverified_blindness", true);

        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(4))
                .build();

        getServer().getPluginManager().registerEvents(this, this);
        if (getCommand("verify") != null) {
            getCommand("verify").setExecutor(this);
        }

        getLogger().info("CloudVerificationPlugin enabled. API: " + apiUrl + ", API Key set: " + (!this.apiKey.isEmpty()));
    }


    @Override
    public void onDisable() {
        unverifiedPlayers.clear();
    }

    @EventHandler(priority = EventPriority.HIGHEST)
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        UUID uuid = player.getUniqueId();

        // Check backend asynchronously
        Bukkit.getScheduler().runTaskAsynchronously(this, () -> {
            boolean isLinked = checkPlayerLinked(uuid);
            Bukkit.getScheduler().runTask(this, () -> {
                if (!isLinked) {
                    unverifiedPlayers.add(uuid);
                    applyRestrictions(player);
                    player.sendMessage(ChatColor.GOLD + "=============================================");
                    player.sendMessage(ChatColor.YELLOW + "Welcome to the Minecraft Server!");
                    player.sendMessage(ChatColor.RED + "Your account is not verified.");
                    player.sendMessage(ChatColor.WHITE + "Generate a code on the web dashboard and type:");
                    player.sendMessage(ChatColor.AQUA + "/verify <code>");
                    player.sendMessage(ChatColor.GOLD + "=============================================");
                } else {
                    unverifiedPlayers.remove(uuid);
                    player.sendMessage(ChatColor.GREEN + "Account verified! Welcome back.");
                }
            });
        });
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        unverifiedPlayers.remove(event.getPlayer().getUniqueId());
    }

    private void applyRestrictions(Player player) {
        if (blindness) {
            player.addPotionEffect(new PotionEffect(PotionEffectType.BLINDNESS, Integer.MAX_VALUE, 1, false, false));
        }
    }

    private void removeRestrictions(Player player) {
        if (blindness) {
            player.removePotionEffect(PotionEffectType.BLINDNESS);
        }
    }

    @EventHandler
    public void onPlayerMove(PlayerMoveEvent event) {
        if (freeze && unverifiedPlayers.contains(event.getPlayer().getUniqueId())) {
            // Prevent changing X or Z coordinate
            if (event.getFrom().getX() != event.getTo().getX() || event.getFrom().getZ() != event.getTo().getZ()) {
                event.setTo(event.getFrom());
            }
        }
    }

    @EventHandler
    public void onBlockBreak(BlockBreakEvent event) {
        if (unverifiedPlayers.contains(event.getPlayer().getUniqueId())) {
            event.setCancelled(true);
            event.getPlayer().sendMessage(ChatColor.RED + "You must verify your account with /verify <code> first.");
        }
    }

    @EventHandler
    public void onBlockPlace(BlockPlaceEvent event) {
        if (unverifiedPlayers.contains(event.getPlayer().getUniqueId())) {
            event.setCancelled(true);
            event.getPlayer().sendMessage(ChatColor.RED + "You must verify your account with /verify <code> first.");
        }
    }

    @EventHandler
    public void onPlayerInteract(PlayerInteractEvent event) {
        if (unverifiedPlayers.contains(event.getPlayer().getUniqueId())) {
            event.setCancelled(true);
        }
    }

    @EventHandler
    public void onEntityDamage(EntityDamageEvent event) {
        if (event.getEntity() instanceof Player player) {
            if (unverifiedPlayers.contains(player.getUniqueId())) {
                event.setCancelled(true);
            }
        }
    }

    @EventHandler
    public void onEntityDamageByEntity(EntityDamageByEntityEvent event) {
        if (event.getDamager() instanceof Player player) {
            if (unverifiedPlayers.contains(player.getUniqueId())) {
                event.setCancelled(true);
            }
        }
    }

    @EventHandler
    public void onPlayerChat(AsyncPlayerChatEvent event) {
        if (unverifiedPlayers.contains(event.getPlayer().getUniqueId())) {
            event.setCancelled(true);
            event.getPlayer().sendMessage(ChatColor.RED + "Chat is disabled until verified. Use /verify <code>.");
        }
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage("This command can only be executed by a player.");
            return true;
        }

        if (args.length < 1) {
            player.sendMessage(ChatColor.RED + "Usage: /verify <code>");
            return true;
        }

        String code = args[0].trim().toUpperCase();
        player.sendMessage(ChatColor.YELLOW + "Verifying code...");

        Bukkit.getScheduler().runTaskAsynchronously(this, () -> {
            String error = submitVerification(code, player.getUniqueId(), player.getName());
            Bukkit.getScheduler().runTask(this, () -> {
                if (error == null) {
                    unverifiedPlayers.remove(player.getUniqueId());
                    removeRestrictions(player);
                    player.sendMessage(ChatColor.GREEN + "Account successfully linked and verified! Have fun!");
                } else {
                    player.sendMessage(ChatColor.RED + "Verification failed: " + error);
                }
            });
        });

        return true;
    }

    private boolean checkPlayerLinked(UUID uuid) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(apiUrl + "/player/" + uuid.toString()))
                    .header("X-Plugin-Api-Key", apiKey)
                    .GET()
                    .timeout(Duration.ofSeconds(3))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200) {
                JsonObject json = JsonParser.parseString(response.body()).getAsJsonObject();
                return json.has("verified") && json.get("verified").getAsBoolean();
            } else {
                getLogger().warning("Player check HTTP " + response.statusCode() + ": " + response.body());
            }
        } catch (Exception e) {
            getLogger().warning("Error querying player verification: " + e.getMessage());
        }
        return false;
    }

    private String submitVerification(String code, UUID uuid, String username) {
        try {
            JsonObject payload = new JsonObject();
            payload.addProperty("code", code);
            payload.addProperty("minecraft_uuid", uuid.toString());
            payload.addProperty("minecraft_username", username);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(apiUrl + "/verify"))
                    .header("Content-Type", "application/json")
                    .header("X-Plugin-Api-Key", apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                    .timeout(Duration.ofSeconds(5))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200) {
                return null;
            } else {
                getLogger().warning("Verification HTTP " + response.statusCode() + ": " + response.body());
                try {
                    JsonObject json = JsonParser.parseString(response.body()).getAsJsonObject();
                    if (json.has("detail")) {
                        return json.get("detail").getAsString();
                    }
                } catch (Exception ignored) {}
                return "HTTP " + response.statusCode();
            }
        } catch (Exception e) {
            getLogger().warning("Error sending verification request: " + e.getMessage());
            return e.getMessage();
        }
    }
}

