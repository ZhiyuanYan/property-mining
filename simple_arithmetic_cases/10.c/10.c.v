module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [15:0] x,
    output reg [15:0] y
);

    // reg [10:0] x_init;
    // reg [10:0] y_init;
    // assume property ((x_init<=2)&&(x_init>=0));
    // assume property ((y_init<=2)&&(y_init>=0));
    // initial begin
    //     x = $random % 3;
    //     y = $random % 3;
    // end
    always @(posedge clk) begin
        if(rst)begin
            x<=2;
            y<=0;
        end
        else begin
            if(selector)begin
                x <= x + 2;
                y <= y + 1;
            end
            else begin
                x  <= x;
                y <= y;
            end
        end
    end
    assert property (!((y==0)&&(x==4)));
endmodule